# Onboarding page — select an employee and generate a full onboarding plan
import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Hardcoded employee options for the selectbox (id, name, role, department, manager)
EMPLOYEE_OPTIONS = {
    "Arjun Mehta — Senior SDE (Software Engineering)": {
        "employee_id": 1, "employee_name": "Arjun Mehta",
        "role": "Senior SDE", "department": "Software Engineering", "manager_name": "Tech Lead"
    },
    "Priya Sharma — SDE II (Software Engineering)": {
        "employee_id": 2, "employee_name": "Priya Sharma",
        "role": "SDE II", "department": "Software Engineering", "manager_name": "Tech Lead"
    },
    "Suresh Reddy — Ops Manager (Operations)": {
        "employee_id": 5, "employee_name": "Suresh Reddy",
        "role": "Ops Manager", "department": "Operations", "manager_name": "VP Operations"
    },
    "Kavita Nair — Process Analyst (Operations)": {
        "employee_id": 6, "employee_name": "Kavita Nair",
        "role": "Process Analyst", "department": "Operations", "manager_name": "Ops Manager"
    },
    "Sunita Joshi — Account Executive (Sales)": {
        "employee_id": 8, "employee_name": "Sunita Joshi",
        "role": "Account Executive", "department": "Sales", "manager_name": "Sales Manager"
    },
    "Vijay Patel — Sales Manager (Sales)": {
        "employee_id": 9, "employee_name": "Vijay Patel",
        "role": "Sales Manager", "department": "Sales", "manager_name": "VP Sales"
    },
}


def render():
    """Render the onboarding plan generation page."""
    st.title("📋 Onboarding Plan Generator")
    st.markdown("Select an employee to generate a comprehensive AI-powered onboarding plan.")
    st.markdown("---")

    with st.form("onboarding_form"):
        selected = st.selectbox("Select Employee", list(EMPLOYEE_OPTIONS.keys()))
        submitted = st.form_submit_button("🚀 Generate Onboarding Plan", use_container_width=True)

    if submitted:
        emp = EMPLOYEE_OPTIONS[selected]

        with st.spinner("🤖 AI is generating the onboarding plan... This may take 60-90 seconds."):
            try:
                response = httpx.post(
                    f"{BACKEND_URL}/onboarding/generate",
                    json=emp,
                    timeout=120.0
                )
                response.raise_for_status()
                result = response.json()
            except httpx.HTTPStatusError as e:
                st.error(f"Backend error: {e.response.status_code} — {e.response.text}")
                return
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
                return

        # Display results in tabs
        st.markdown("---")
        st.subheader(f"📋 Onboarding Plan for {emp['employee_name']}")

        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Checklist", "📚 Training Roadmap", "🔧 Tools Access", "📅 First Week"
        ])

        with tab1:
            st.markdown("#### 30-Day Onboarding Checklist")
            if result["checklist"]:
                for item in result["checklist"]:
                    st.markdown(
                        f"- **Day {item.get('day', '?')}** — {item.get('task', '')} "
                        f"_(Owner: {item.get('owner', 'TBD')} | Category: {item.get('category', 'N/A')})_"
                    )
            else:
                st.info("No checklist items generated.")

        with tab2:
            st.markdown("#### 90-Day Training Roadmap")
            if result["training_roadmap"]:
                for item in result["training_roadmap"]:
                    st.markdown(
                        f"- **Week {item.get('week', '?')}** — {item.get('topic', '')} "
                        f"_({item.get('type', 'N/A')})_ → {item.get('outcome', '')}"
                    )
            else:
                st.info("No training roadmap generated.")

        with tab3:
            st.markdown("#### Tools & System Access")
            if result["tools_access"]:
                for item in result["tools_access"]:
                    priority_emoji = {"day-1": "🔴", "week-1": "🟡", "month-1": "🟢"}.get(
                        item.get("priority", ""), "⚪"
                    )
                    st.markdown(
                        f"- {priority_emoji} **{item.get('tool', '')}** — {item.get('purpose', '')} "
                        f"_(Priority: {item.get('priority', 'N/A')})_"
                    )
            else:
                st.info("No tools access list generated.")

        with tab4:
            st.markdown("#### First Week Schedule")
            if result["first_week"]:
                for day_schedule in result["first_week"]:
                    st.markdown(f"**{day_schedule.get('day', 'Day')}**")
                    for activity in day_schedule.get("activities", []):
                        st.markdown(
                            f"  - 🕐 {activity.get('time', '')} — {activity.get('activity', '')} "
                            f"_(with {activity.get('with_whom', 'TBD')})_"
                        )
            else:
                st.info("No first week schedule generated.")
