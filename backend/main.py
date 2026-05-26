# FastAPI app — 3 POST endpoints for recruitment, onboarding, and performance
# Run: uvicorn backend.main:app --reload --port 8000
import io
import json
import fitz  # PyMuPDF
import docx  # python-docx
from fastapi import FastAPI, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

from backend.db.database import init_db, get_db
from backend.db.models import Candidate, OnboardingPlan, PerformanceReview
from backend.agents.recruitment import recruitment_graph
from backend.agents.onboarding import onboarding_graph
from backend.agents.performance import performance_graph

app = FastAPI(title="HRMS AI Portal", version="1.0.0")

# --- LLM instance for resume validation (lightweight check) ---
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0)

# --- Hardcoded response: corrupted or unreadable file ---
CORRUPTED_FILE_RESPONSE = {
    "candidate_id": None,
    "candidate_name": "Unknown",
    "applied_role": "Unknown",
    "overall_score": 0.0,
    "skill_score": 0.0,
    "recommendation": "no",
    "reasoning": (
        "The uploaded resume could not be processed. "
        "The file appears to be corrupted, password-protected, or in an unsupported format. "
        "Please upload a valid PDF (.pdf) or Word document (.docx) and try again."
    ),
    "matched_skills": [],
    "missing_skills": [],
    "interview_questions": [],
}

# --- Hardcoded response: file is not a resume ---
NOT_A_RESUME_RESPONSE = {
    "candidate_id": None,
    "candidate_name": "Unknown",
    "applied_role": "Unknown",
    "overall_score": 0.0,
    "skill_score": 0.0,
    "recommendation": "no",
    "reasoning": (
        "The uploaded document does not appear to be a resume. "
        "We only process candidate resumes. "
        "Please upload a valid resume and try again."
    ),
    "matched_skills": [],
    "missing_skills": [],
    "interview_questions": [],
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyMuPDF.
    Raises ValueError if file is corrupted, empty, or image-only.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        if doc.page_count == 0:
            doc.close()
            raise ValueError("PDF has no pages.")

        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        if not text.strip():
            raise ValueError(
                "PDF contains no extractable text (possibly a scanned image)."
            )

        return text

    except fitz.FileDataError:
        raise ValueError("File is corrupted or not a valid PDF.")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {str(e)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from .docx bytes using python-docx.
    Raises ValueError if file is corrupted or not a valid docx.
    """
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join(para.text for para in doc.paragraphs)

        if not text.strip():
            raise ValueError("DOCX contains no extractable text.")

        return text

    except Exception as e:
        raise ValueError(f"DOCX extraction failed: {str(e)}")


def extract_text_from_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Route to the correct extractor based on file extension or content type.
    Raises ValueError for unsupported or corrupted files.
    """
    name_lower = filename.lower()

    if name_lower.endswith(".pdf") or content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)

    if name_lower.endswith(".docx") or "wordprocessingml" in content_type:
        return extract_text_from_docx(file_bytes)

    raise ValueError(
        f"Unsupported file type '{filename}'. Please upload a PDF or DOCX resume."
    )


def is_resume(text: str) -> bool:
    """
    Ask the LLM if the extracted text is a resume.
    Returns True if it looks like a resume, False otherwise.
    Uses only the first 2000 chars to keep it fast and cheap.
    """
    snippet = text[:2000]
    result = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a document classifier. "
                    "Your only job is to decide if the given text is a resume or CV. "
                    "A resume typically contains: name, contact info, work experience, education, skills. "
                    "Reply with ONLY one word: YES or NO. Nothing else."
                )
            ),
            HumanMessage(content=f"Is this a resume?\n\n{snippet}"),
        ]
    )
    answer = result.content.strip().upper()
    return answer.startswith("YES")


@app.on_event("startup")
def on_startup():
    """Initialize the database tables on server start."""
    init_db()


@app.post("/recruitment/analyze")
def analyze_candidate(
    candidate_name: str = Form(...),
    applied_role: str = Form(...),
    department: str = Form(...),
    job_description: str = Form(...),
    resume_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Parse a PDF or DOCX resume, validate it, run the recruitment graph, save and return results."""

    file_bytes = resume_file.file.read()

    # --- Step 1: Extract text (corrupted file guard) ---
    try:
        resume_text = extract_text_from_file(
            file_bytes, resume_file.filename or "", resume_file.content_type or ""
        )
    except ValueError:
        response = dict(CORRUPTED_FILE_RESPONSE)
        response["candidate_name"] = candidate_name
        response["applied_role"] = applied_role
        return response

    # --- Step 2: Check if document is actually a resume ---
    if not is_resume(resume_text):
        response = dict(NOT_A_RESUME_RESPONSE)
        response["candidate_name"] = candidate_name
        response["applied_role"] = applied_role
        return response

    # --- Step 3: Run recruitment graph ---
    initial_state = {
        "resume_text": resume_text,
        "job_description": job_description,
        "candidate_name": candidate_name,
        "applied_role": applied_role,
        "extracted_skills": [],
        "years_experience": 0,
        "matched_skills": [],
        "missing_skills": [],
        "skill_score": 0.0,
        "overall_score": 0.0,
        "interview_questions": [],
        "recommendation": "",
        "reasoning": "",
    }

    result = recruitment_graph.invoke(initial_state)

    candidate = Candidate(
        name=result["candidate_name"],
        applied_role=result["applied_role"],
        department=department,
        overall_score=result["overall_score"],
        skill_score=result["skill_score"],
        recommendation=result["recommendation"],
        matched_skills=json.dumps(result["matched_skills"]),
        missing_skills=json.dumps(result["missing_skills"]),
        interview_questions=json.dumps(result["interview_questions"]),
        reasoning=result["reasoning"],
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "candidate_id": candidate.id,
        "candidate_name": result["candidate_name"],
        "applied_role": result["applied_role"],
        "overall_score": result["overall_score"],
        "skill_score": result["skill_score"],
        "recommendation": result["recommendation"],
        "reasoning": result["reasoning"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "interview_questions": result["interview_questions"],
    }


@app.post("/onboarding/generate")
def generate_onboarding(data: dict, db: Session = Depends(get_db)):
    """Run the onboarding graph and save the generated plan."""
    initial_state = {
        "employee_name": data["employee_name"],
        "role": data["role"],
        "department": data["department"],
        "manager_name": data["manager_name"],
        "dept_tools": [],
        "dept_focus": [],
        "checklist": [],
        "training_roadmap": [],
        "tools_access": [],
        "first_week": [],
    }

    result = onboarding_graph.invoke(initial_state)

    plan = OnboardingPlan(
        employee_id=data["employee_id"],
        checklist=json.dumps(result["checklist"]),
        training_roadmap=json.dumps(result["training_roadmap"]),
        tools_access=json.dumps(result["tools_access"]),
        first_week=json.dumps(result["first_week"]),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {
        "plan_id": plan.id,
        "employee_name": data["employee_name"],
        "checklist": result["checklist"],
        "training_roadmap": result["training_roadmap"],
        "tools_access": result["tools_access"],
        "first_week": result["first_week"],
    }


@app.post("/performance/review")
def generate_review(data: dict, db: Session = Depends(get_db)):
    """Run the performance review graph and save the generated review."""
    initial_state = {
        "employee_name": data["employee_name"],
        "role": data["role"],
        "department": data["department"],
        "review_period": data["review_period"],
        "attendance_score": float(data["attendance_score"]),
        "kpi_score": float(data["kpi_score"]),
        "task_completion": float(data["task_completion"]),
        "manager_feedback": data["manager_feedback"],
        "peer_feedback": data["peer_feedback"],
        "self_assessment": data["self_assessment"],
        "weighted_score": 0.0,
        "rating_tier": "",
        "strengths": [],
        "weaknesses": [],
        "summary": "",
        "overall_rating": "",
        "recommendations": [],
    }

    result = performance_graph.invoke(initial_state)

    review = PerformanceReview(
        employee_id=data["employee_id"],
        review_period=data["review_period"],
        weighted_score=result["weighted_score"],
        overall_rating=result["overall_rating"],
        strengths=json.dumps(result["strengths"]),
        weaknesses=json.dumps(result["weaknesses"]),
        summary=result["summary"],
        recommendations=json.dumps(result["recommendations"]),
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return {
        "review_id": review.id,
        "employee_name": data["employee_name"],
        "review_period": data["review_period"],
        "weighted_score": result["weighted_score"],
        "overall_rating": result["overall_rating"],
        "strengths": result["strengths"],
        "weaknesses": result["weaknesses"],
        "summary": result["summary"],
        "recommendations": result["recommendations"],
    }
