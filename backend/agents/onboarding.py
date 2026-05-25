# Onboarding agent — LangGraph workflow for generating structured onboarding plans
import time
from typing import List, TypedDict
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# --- Department context lookup (hardcoded, not DB) ---

DEPARTMENT_CONTEXT = {
    "Software Engineering": {
        "tools": ["GitHub", "Jira", "AWS Console", "Confluence", "Slack"],
        "focus": ["codebase walkthrough", "CI/CD", "architecture review", "sprint ceremonies"]
    },
    "Operations": {
        "tools": ["ERP System", "Google Workspace", "Trello", "Slack", "PowerBI"],
        "focus": ["process docs", "SLA understanding", "vendor contacts", "reporting"]
    },
    "Sales": {
        "tools": ["Salesforce CRM", "HubSpot", "LinkedIn Sales Nav", "Zoom", "Slack"],
        "focus": ["product training", "sales playbook", "ICP understanding", "CRM hygiene"]
    }
}


# --- Pydantic schemas ---

# Single checklist item for the 30-day onboarding
class ChecklistItem(BaseModel):
    task: str = Field(description="Description of the onboarding task")
    day: int = Field(description="Target day number (1-30)")
    owner: str = Field(description="Person responsible: employee, manager, HR, or IT")
    category: str = Field(description="Category: administrative, technical, social, or training")


# Wrapper for the full checklist
class Checklist(BaseModel):
    checklist: List[ChecklistItem] = Field(description="12-15 onboarding tasks across 30 days")


# Single training roadmap milestone
class RoadmapItem(BaseModel):
    week: int = Field(description="Week number (1-12)")
    topic: str = Field(description="Training topic or focus area")
    type: str = Field(description="Type: hands-on, shadowing, workshop, self-study, or assessment")
    outcome: str = Field(description="Expected outcome or deliverable")


# Wrapper for the full training roadmap
class TrainingRoadmap(BaseModel):
    roadmap: List[RoadmapItem] = Field(description="90-day training roadmap with weekly milestones")


# Single tool access entry
class ToolItem(BaseModel):
    tool: str = Field(description="Name of the tool or system")
    purpose: str = Field(description="Why the employee needs this tool")
    priority: str = Field(description="Priority: day-1, week-1, or month-1")


# Wrapper for all tools
class ToolsList(BaseModel):
    tools: List[ToolItem] = Field(description="Tools and system access needed")


# Single activity in a day
class DayActivity(BaseModel):
    time: str = Field(description="Time slot, e.g. '9:00 AM - 10:00 AM'")
    activity: str = Field(description="What the employee will do")
    with_whom: str = Field(description="Who they'll do it with")


# Full schedule for one day
class DaySchedule(BaseModel):
    day: str = Field(description="Day label, e.g. 'Monday' or 'Day 1'")
    activities: List[DayActivity] = Field(description="Scheduled activities for this day")


# First week schedule wrapper
class FirstWeek(BaseModel):
    schedule: List[DaySchedule] = Field(description="5-day first week schedule")


# --- LangGraph state ---

class OnboardingState(TypedDict):
    employee_name: str
    role: str
    department: str
    manager_name: str
    dept_tools: List[str]
    dept_focus: List[str]
    checklist: List[dict]
    training_roadmap: List[dict]
    tools_access: List[dict]
    first_week: List[dict]


# --- LLM instance ---

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)


# --- Node functions ---

def load_dept_context(state: OnboardingState) -> dict:
    """Inject department-specific tools and focus areas into state (no LLM call)."""
    dept = state["department"]
    ctx = DEPARTMENT_CONTEXT.get(dept, DEPARTMENT_CONTEXT["Software Engineering"])
    return {
        "dept_tools": ctx["tools"],
        "dept_focus": ctx["focus"]
    }


def gen_checklist(state: OnboardingState) -> dict:
    """Generate a 30-day onboarding checklist tailored to department and role."""
    structured_llm = llm.with_structured_output(Checklist)
    prompt = (
        f"New hire: {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Department: {state['department']}\n"
        f"Manager: {state['manager_name']}\n"
        f"Department tools: {', '.join(state['dept_tools'])}\n"
        f"Department focus areas: {', '.join(state['dept_focus'])}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="Create a 30-day onboarding checklist for a new hire. Include 12-15 tasks spanning administrative setup, technical onboarding, social integration, and training. Assign each task to the appropriate owner."),
        HumanMessage(content=prompt)
    ])
    time.sleep(2)
    return {"checklist": [item.model_dump() for item in result.checklist]}


def gen_training_roadmap(state: OnboardingState) -> dict:
    """Generate a 90-day training roadmap with weekly milestones."""
    structured_llm = llm.with_structured_output(TrainingRoadmap)
    prompt = (
        f"Employee: {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Department: {state['department']}\n"
        f"Focus areas: {', '.join(state['dept_focus'])}\n"
        f"Tools to learn: {', '.join(state['dept_tools'])}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="Create a 90-day training roadmap with weekly milestones. Include a mix of hands-on tasks, shadowing, workshops, self-study, and assessments."),
        HumanMessage(content=prompt)
    ])
    time.sleep(2)
    return {"training_roadmap": [item.model_dump() for item in result.roadmap]}


def gen_tools_access(state: OnboardingState) -> dict:
    """List all tools and system access the employee needs with priorities."""
    structured_llm = llm.with_structured_output(ToolsList)
    prompt = (
        f"Employee: {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Department: {state['department']}\n"
        f"Department tools: {', '.join(state['dept_tools'])}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="List the tools and system access this employee needs, with priorities (day-1, week-1, or month-1). Include department-specific tools and general company tools."),
        HumanMessage(content=prompt)
    ])
    time.sleep(2)
    return {"tools_access": [item.model_dump() for item in result.tools]}


def gen_first_week(state: OnboardingState) -> dict:
    """Design a structured and welcoming first-week schedule."""
    structured_llm = llm.with_structured_output(FirstWeek)
    prompt = (
        f"Employee: {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Department: {state['department']}\n"
        f"Manager: {state['manager_name']}\n"
        f"Focus areas: {', '.join(state['dept_focus'])}\n"
        f"Tools: {', '.join(state['dept_tools'])}"
    )
    result = structured_llm.invoke([
        SystemMessage(content="Design a welcoming, structured first-week schedule (5 days). Balance orientation, introductions, initial training, and social activities. Don't make it overwhelming."),
        HumanMessage(content=prompt)
    ])
    return {"first_week": [day.model_dump() for day in result.schedule]}


# --- Compile graph at module level ---

workflow = StateGraph(OnboardingState)
workflow.add_node("load_dept_context", load_dept_context)
workflow.add_node("gen_checklist", gen_checklist)
workflow.add_node("gen_training_roadmap", gen_training_roadmap)
workflow.add_node("gen_tools_access", gen_tools_access)
workflow.add_node("gen_first_week", gen_first_week)

workflow.set_entry_point("load_dept_context")
workflow.add_edge("load_dept_context", "gen_checklist")
workflow.add_edge("gen_checklist", "gen_training_roadmap")
workflow.add_edge("gen_training_roadmap", "gen_tools_access")
workflow.add_edge("gen_tools_access", "gen_first_week")
workflow.add_edge("gen_first_week", END)

onboarding_graph = workflow.compile()
