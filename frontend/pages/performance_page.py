# Performance review page — input scores and feedback, get AI-generated review
import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Hardcoded employee options (id, name, role, department)
EMPLOYEE_OPTIONS = {
    "Arjun Mehta — Senior SDE (Software Engineering)": {
        "employee_id": 1, "employee_name": "Arjun Mehta",
        "role": "Senior SDE", "department": "Software Engineering"
    },
    "Priya Sharma — SDE II (Software Engineering)": {
        "employee_id": 2, "employee_name": "Priya Sharma",
        "role": "SDE II", "department": "Software Engineering"
    },
    "Suresh Reddy — Ops Manager (Operations)": {
        "employee_id": 5, "employee_name": "Suresh Reddy",
        "role": "Ops Manager", "department": "Operations"
    },
    "Kavita Nair — Process Analyst (Operations)": {
        "employee_id": 6, "employee_name": "Kavita Nair",
        "role": "Process Analyst", "department": "Operations"
    },
    "Sunita Joshi — Account Executive (Sales)": {
        "employee_id": 8, "employee_name": "Sunita Joshi",
        "role": "Account Executive", "department": "Sales"
    },
    "Vijay Patel — Sales Manager (Sales)": {
        "employee_id": 9, "employee_name": "Vijay Patel",
        "role": "Sales Manager", "department": "Sales"
    },
}

REVIEW_PERIODS = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]


def render():
    """Render the performance review page."""
    st.title("📊 Performance Review Generator")
    st.markdown("Input performance data and feedback to generate an AI-powered performance review.")
    st.markdown("---")

    with st.form("performance_form"):
        # Employee and period selection
        col1, col2 = st.columns(2)
        with col1:
            selected = st.selectbox("Select Employee", list(EMPLOYEE_OPTIONS.keys()))
        with col2:
            review_period = st.selectbox("Review Period", REVIEW_PERIODS)

        st.markdown("#### 📈 Performance Scores")
        s1, s2, s3 = st.columns(3)
        with s1:
            attendance_score = st.slider("Attendance Score", 0.0, 10.0, 7.0, 0.5)
        with s2:
            kpi_score = st.slider("KPI Score", 0.0, 10.0, 7.0, 0.5)
        with s3:
            task_completion = st.slider("Task Completion (%)", 0, 100, 75, 5)

        # Live weighted score preview
        weighted_preview = (
            kpi_score * 0.40
            + (task_completion / 10) * 0.40
            + attendance_score * 0.20
        )
        if weighted_preview >= 8.5:
            tier_preview = "🟢 Exceptional"
        elif weighted_preview >= 6.0:
            tier_preview = "🟡 Meets Expectations"
        else:
            tier_preview = "🔴 Needs Improvement"

        st.info(f"**Weighted Score Preview:** {weighted_preview:.2f} / 10 — {tier_preview}")

        st.markdown("#### 💬 Feedback")
        manager_feedback = st.text_area(
            "Manager Feedback",
            height=100,
            placeholder="Describe the employee's performance from a manager's perspective..."
        )
        peer_feedback = st.text_area(
            "Peer Feedback",
            height=100,
            placeholder="Describe the employee's collaboration and teamwork..."
        )
        self_assessment = st.text_area(
            "Self Assessment",
            height=100,
            placeholder="Employee's own reflection on their performance..."
        )

        submitted = st.form_submit_button("📝 Generate Review", use_container_width=True)

    if submitted:
        if not manager_feedback or not peer_feedback or not self_assessment:
            st.error("Please fill in all three feedback fields.")
            return

        emp = EMPLOYEE_OPTIONS[selected]
        payload = {
            "employee_id": emp["employee_id"],
            "employee_name": emp["employee_name"],
            "role": emp["role"],
            "department": emp["department"],
            "review_period": review_period,
            "attendance_score": attendance_score,
            "kpi_score": kpi_score,
            "task_completion": task_completion,
            "manager_feedback": manager_feedback,
            "peer_feedback": peer_feedback,
            "self_assessment": self_assessment
        }

        with st.spinner("🤖 AI is generating the performance review... This may take 60-90 seconds."):
            try:
                response = httpx.post(
                    f"{BACKEND_URL}/performance/review",
                    json=payload,
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

        # Display results
        st.markdown("---")
        st.subheader("📊 Performance Review Results")

        # Overall rating and score
        st.success(
            f"**Overall Rating:** {result['overall_rating']} | "
            f"**Weighted Score:** {result['weighted_score']:.2f} / 10"
        )

        # Summary
        st.markdown("#### 📝 Performance Summary")
        st.write(result["summary"])

        # Strengths and growth areas
        col_str, col_weak = st.columns(2)
        with col_str:
            st.markdown("#### 💪 Key Strengths")
            if result["strengths"]:
                for s in result["strengths"]:
                    st.markdown(f"- ✅ {s}")
            else:
                st.info("No strengths identified.")

        with col_weak:
            st.markdown("#### 🌱 Growth Areas")
            if result["weaknesses"]:
                for w in result["weaknesses"]:
                    st.markdown(f"- 📌 {w}")
            else:
                st.info("No growth areas identified.")

        # Recommendations
        if result.get("recommendations"):
            st.markdown("---")
            st.markdown("#### 🎯 Recommendations")
            for i, rec in enumerate(result["recommendations"], 1):
                st.markdown(
                    f"**{i}. {rec.get('action', '')}**\n"
                    f"   - ⏰ Timeline: {rec.get('timeline', 'N/A')}\n"
                    f"   - 👤 Owner: {rec.get('owner', 'N/A')}"
                )
