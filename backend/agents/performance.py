# Performance review agent — LangGraph workflow for AI-powered performance reviews
import time
from typing import List, TypedDict
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# --- Pydantic schemas ---

# Key strengths identified from performance data
class Strengths(BaseModel):
    strengths: List[str] = Field(description="3-4 specific, concrete strengths")


# Development areas framed constructively
class Weaknesses(BaseModel):
    weaknesses: List[str] = Field(description="2-3 development areas framed as growth opportunities")


# Overall performance summary with rating
class Summary(BaseModel):
    summary: str = Field(description="2-paragraph professional performance summary")
    overall_rating: str = Field(description="One of: Exceptional Performer, Solid Contributor, Needs Development")


# Single actionable recommendation
class RecommendationItem(BaseModel):
    action: str = Field(description="Specific SMART action to take")
    timeline: str = Field(description="Timeline for completion")
    owner: str = Field(description="Person responsible: employee, manager, or HR")


# Wrapper for all recommendations
class Recommendations(BaseModel):
    recommendations: List[RecommendationItem] = Field(description="3-4 actionable SMART recommendations")


# --- LangGraph state ---

class PerformanceState(TypedDict):
    employee_name: str
    role: str
    department: str
    review_period: str
    attendance_score: float
    kpi_score: float
    task_completion: float
    manager_feedback: str
    peer_feedback: str
    self_assessment: str
    weighted_score: float
    rating_tier: str
    strengths: List[str]
    weaknesses: List[str]
    summary: str
    overall_rating: str
    recommendations: List[dict]


# --- LLM instance ---

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)

# --- Tier-specific instruction for recommendations ---

TIER_INSTRUCTIONS = {
    "exceptional": "Focus on stretch goals, leadership opportunities, and retention strategies.",
    "meets_expectations": "Focus on skill deepening and incremental growth opportunities.",
    "needs_improvement": "Focus on specific corrective actions with clear timelines and support structures."
}


# --- Node functions ---

def compute_weighted_score(state: PerformanceState) -> dict:
    """Calculate weighted score and rating tier using pure math (no LLM)."""
    weighted = (
        state["kpi_score"] * 0.40
        + (state["task_completion"] / 10) * 0.40
        + state["attendance_score"] * 0.20
    )
    if weighted >= 8.5:
        tier = "exceptional"
    elif weighted >= 6.0:
        tier = "meets_expectations"
    else:
        tier = "needs_improvement"
    return {
        "weighted_score": round(weighted, 2),
        "rating_tier": tier
    }


def analyze_strengths(state: PerformanceState) -> dict:
    """Identify 3-4 concrete strengths from the performance data."""
    structured_llm = llm.with_structured_output(Strengths)
    prompt = (
        f"Employee: {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Department: {state['department']}\n"
        f"Review period: {state['review_period']}\n"
        f"Weighted score: {state['weighted_score']} / 10\n"
        f"Rating tier: {state['rating_tier']}\n"
        f"KPI score: {state['kpi_score']}/10\n"
        f"Task completion: {state['task_completion']}%\n"
        f"Attendance: {state['attendance_score']}/10\n\n"
        f"Manager feedback: {state['manager_feedback']}\n"
        f"Peer feedback: {state['peer_feedback']}\n"
        f"Self assessment: {state['self_assessment']}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="Identify 3-4 specific, concrete strengths from this performance data. Base your analysis on the scores, feedback, and self-assessment. Be specific — reference actual behaviors and outcomes."),
        HumanMessage(content=prompt)
    ])
    time.sleep(2)
    return {"strengths": result.strengths}


def analyze_weaknesses(state: PerformanceState) -> dict:
    """Identify 2-3 development areas, framed constructively."""
    structured_llm = llm.with_structured_output(Weaknesses)
    prompt = (
        f"Employee: {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Department: {state['department']}\n"
        f"Weighted score: {state['weighted_score']} / 10\n"
        f"Rating tier: {state['rating_tier']}\n"
        f"KPI score: {state['kpi_score']}/10\n"
        f"Task completion: {state['task_completion']}%\n"
        f"Attendance: {state['attendance_score']}/10\n\n"
        f"Manager feedback: {state['manager_feedback']}\n"
        f"Peer feedback: {state['peer_feedback']}\n"
        f"Self assessment: {state['self_assessment']}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="Identify 2-3 development areas. Frame them constructively as growth opportunities, not criticisms. Be specific and actionable."),
        HumanMessage(content=prompt)
    ])
    time.sleep(2)
    return {"weaknesses": result.weaknesses}


def gen_summary(state: PerformanceState) -> dict:
    """Write a professional 2-paragraph performance summary."""
    structured_llm = llm.with_structured_output(Summary)
    prompt = (
        f"Employee: {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Department: {state['department']}\n"
        f"Review period: {state['review_period']}\n"
        f"Weighted score: {state['weighted_score']} / 10\n"
        f"Rating tier: {state['rating_tier']}\n"
        f"Strengths: {', '.join(state['strengths'])}\n"
        f"Growth areas: {', '.join(state['weaknesses'])}\n\n"
        f"Manager feedback: {state['manager_feedback']}\n"
        f"Self assessment: {state['self_assessment']}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="Write a 2-paragraph professional performance summary. Be specific, warm, and balanced. Use the overall_rating field to assign one of: Exceptional Performer, Solid Contributor, Needs Development."),
        HumanMessage(content=prompt)
    ])
    time.sleep(2)
    return {
        "summary": result.summary,
        "overall_rating": result.overall_rating
    }


def gen_recommendations(state: PerformanceState) -> dict:
    """Create 3-4 actionable SMART recommendations based on rating tier."""
    structured_llm = llm.with_structured_output(Recommendations)
    tier_instruction = TIER_INSTRUCTIONS.get(state["rating_tier"], TIER_INSTRUCTIONS["meets_expectations"])
    prompt = (
        f"Employee: {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Department: {state['department']}\n"
        f"Weighted score: {state['weighted_score']} / 10\n"
        f"Rating tier: {state['rating_tier']}\n"
        f"Strengths: {', '.join(state['strengths'])}\n"
        f"Growth areas: {', '.join(state['weaknesses'])}\n"
        f"Summary: {state['summary']}"
    )
    result = structured_llm.invoke([
        SystemMessage(content=f"Create 3-4 actionable SMART recommendations. {tier_instruction}"),
        HumanMessage(content=prompt)
    ])
    return {"recommendations": [r.model_dump() for r in result.recommendations]}


# --- Compile graph at module level ---

workflow = StateGraph(PerformanceState)
workflow.add_node("compute_weighted_score", compute_weighted_score)
workflow.add_node("analyze_strengths", analyze_strengths)
workflow.add_node("analyze_weaknesses", analyze_weaknesses)
workflow.add_node("gen_summary", gen_summary)
workflow.add_node("gen_recommendations", gen_recommendations)

workflow.set_entry_point("compute_weighted_score")
workflow.add_edge("compute_weighted_score", "analyze_strengths")
workflow.add_edge("analyze_strengths", "analyze_weaknesses")
workflow.add_edge("analyze_weaknesses", "gen_summary")
workflow.add_edge("gen_summary", "gen_recommendations")
workflow.add_edge("gen_recommendations", END)

performance_graph = workflow.compile()
