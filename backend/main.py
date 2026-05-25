# FastAPI app — 3 POST endpoints for recruitment, onboarding, and performance
# Run: uvicorn backend.main:app --reload --port 8000
import json
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from backend.db.database import init_db, get_db
from backend.db.models import Candidate, OnboardingPlan, PerformanceReview
from backend.agents.recruitment import recruitment_graph
from backend.agents.onboarding import onboarding_graph
from backend.agents.performance import performance_graph

app = FastAPI(title="HRMS AI Portal", version="1.0.0")


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
    db: Session = Depends(get_db)
):
    """Parse a PDF resume, run the recruitment graph, save and return results."""
    pdf_bytes = resume_file.file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    resume_text = ""
    for page in doc:
        resume_text += page.get_text()
    doc.close()

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
        "reasoning": ""
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
        reasoning=result["reasoning"]
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
        "interview_questions": result["interview_questions"]
    }


@app.post("/onboarding/generate")
def generate_onboarding(
    data: dict,
    db: Session = Depends(get_db)
):
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
        "first_week": []
    }

    result = onboarding_graph.invoke(initial_state)

    plan = OnboardingPlan(
        employee_id=data["employee_id"],
        checklist=json.dumps(result["checklist"]),
        training_roadmap=json.dumps(result["training_roadmap"]),
        tools_access=json.dumps(result["tools_access"]),
        first_week=json.dumps(result["first_week"])
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
        "first_week": result["first_week"]
    }


@app.post("/performance/review")
def generate_review(
    data: dict,
    db: Session = Depends(get_db)
):
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
        "recommendations": []
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
        recommendations=json.dumps(result["recommendations"])
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
        "recommendations": result["recommendations"]
    }
