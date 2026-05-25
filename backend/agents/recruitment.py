# Recruitment agent — LangGraph workflow for resume screening and candidate scoring
import time
from typing import List, TypedDict
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# --- Pydantic schemas for structured LLM outputs ---

# Extracted skills and experience from a resume
class SkillExtraction(BaseModel):
    skills: List[str] = Field(description="List of technical and soft skills found in the resume")
    years_experience: int = Field(description="Total years of professional experience")


# Candidate scoring against a job description
class CandidateScore(BaseModel):
    overall_score: float = Field(description="Overall candidate score from 0 to 10")
    skill_score: float = Field(description="Skill match score from 0 to 10")
    matched_skills: List[str] = Field(description="Skills that match the job description")
    missing_skills: List[str] = Field(description="Required skills the candidate lacks")


# Single interview question with type tag
class InterviewQuestion(BaseModel):
    question: str = Field(description="The interview question text")
    type: str = Field(description="Question type: technical or behavioral")


# Wrapper for a list of interview questions
class InterviewQuestions(BaseModel):
    questions: List[InterviewQuestion] = Field(description="List of 5 targeted interview questions")


# Final hiring recommendation with reasoning
class HiringRecommendation(BaseModel):
    recommendation: str = Field(description="One of: strong_yes, yes, maybe, no")
    reasoning: str = Field(description="Concise justification for the recommendation")


# --- LangGraph state ---

class RecruitmentState(TypedDict):
    resume_text: str
    job_description: str
    candidate_name: str
    applied_role: str
    extracted_skills: List[str]
    years_experience: int
    matched_skills: List[str]
    missing_skills: List[str]
    skill_score: float
    overall_score: float
    interview_questions: List[dict]
    recommendation: str
    reasoning: str


# --- LLM instance ---

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)


# --- Node functions ---

def extract_skills(state: RecruitmentState) -> dict:
    """Extract skills and years of experience from the resume text."""
    structured_llm = llm.with_structured_output(SkillExtraction)
    result = structured_llm.invoke([
        SystemMessage(content="Extract skills and years of experience from this resume. Return all technical skills, tools, frameworks, and soft skills you can identify."),
        HumanMessage(content=state["resume_text"])
    ])
    time.sleep(2)
    return {
        "extracted_skills": result.skills,
        "years_experience": result.years_experience
    }


def score_candidate(state: RecruitmentState) -> dict:
    """Score the candidate against the job description."""
    structured_llm = llm.with_structured_output(CandidateScore)
    prompt = (
        f"Candidate skills: {', '.join(state['extracted_skills'])}\n"
        f"Years of experience: {state['years_experience']}\n"
        f"Applied role: {state['applied_role']}\n\n"
        f"Job Description:\n{state['job_description']}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="Score this candidate against the job description. Be objective. Score 0-10. Return overall_score, skill_score, matched_skills, missing_skills."),
        HumanMessage(content=prompt)
    ])
    time.sleep(2)
    return {
        "overall_score": result.overall_score,
        "skill_score": result.skill_score,
        "matched_skills": result.matched_skills,
        "missing_skills": result.missing_skills
    }


def gen_interview_questions(state: RecruitmentState) -> dict:
    """Generate 5 targeted interview questions for high-scoring candidates."""
    structured_llm = llm.with_structured_output(InterviewQuestions)
    prompt = (
        f"Candidate: {state['candidate_name']}\n"
        f"Role: {state['applied_role']}\n"
        f"Matched skills: {', '.join(state['matched_skills'])}\n"
        f"Missing skills: {', '.join(state['missing_skills'])}\n"
        f"Overall score: {state['overall_score']}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="Generate 5 targeted interview questions: 3 technical and 2 behavioral. Focus on verifying matched skills and probing gaps."),
        HumanMessage(content=prompt)
    ])
    time.sleep(2)
    return {
        "interview_questions": [q.model_dump() for q in result.questions]
    }


def hiring_recommendation(state: RecruitmentState) -> dict:
    """Produce a final hiring recommendation based on all collected data."""
    structured_llm = llm.with_structured_output(HiringRecommendation)
    prompt = (
        f"Candidate: {state['candidate_name']}\n"
        f"Role: {state['applied_role']}\n"
        f"Overall score: {state['overall_score']}\n"
        f"Skill score: {state['skill_score']}\n"
        f"Matched skills: {', '.join(state['matched_skills'])}\n"
        f"Missing skills: {', '.join(state['missing_skills'])}\n"
        f"Years experience: {state['years_experience']}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="Give a concise hiring recommendation based on score and skill match. Use one of: strong_yes, yes, maybe, no."),
        HumanMessage(content=prompt)
    ])
    return {
        "recommendation": result.recommendation,
        "reasoning": result.reasoning
    }


# --- Conditional edge ---

def should_generate_questions(state: RecruitmentState) -> str:
    """Route to interview questions if score >= 7.0, otherwise skip to recommendation."""
    if state["overall_score"] >= 7.0:
        return "gen_interview_questions"
    return "hiring_recommendation"


# --- Compile graph at module level ---

workflow = StateGraph(RecruitmentState)
workflow.add_node("extract_skills", extract_skills)
workflow.add_node("score_candidate", score_candidate)
workflow.add_node("gen_interview_questions", gen_interview_questions)
workflow.add_node("hiring_recommendation", hiring_recommendation)

workflow.set_entry_point("extract_skills")
workflow.add_edge("extract_skills", "score_candidate")
workflow.add_conditional_edges("score_candidate", should_generate_questions, {
    "gen_interview_questions": "gen_interview_questions",
    "hiring_recommendation": "hiring_recommendation"
})
workflow.add_edge("gen_interview_questions", "hiring_recommendation")
workflow.add_edge("hiring_recommendation", END)

recruitment_graph = workflow.compile()
