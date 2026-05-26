# Recruitment page — resume upload (PDF or DOCX), job description input, and AI screening results
import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

RECOMMENDATION_EMOJI = {
    "strong_yes": "🟢 Strong Yes",
    "yes": "🟡 Yes",
    "maybe": "🟠 Maybe",
    "no": "🔴 No"
}


def render():
    """Render the recruitment screening page."""
    st.title("🎯 Recruitment Screening")
    st.markdown("Upload a resume and job description to get an AI-powered candidate assessment.")
    st.markdown("---")

    with st.form("recruitment_form"):
        col1, col2 = st.columns(2)

        with col1:
            candidate_name = st.text_input("Candidate Name", placeholder="e.g. John Doe")
            applied_role = st.text_input("Applied Role", placeholder="e.g. Senior Software Engineer")
            department = st.selectbox("Department", ["Software Engineering", "Operations", "Sales"])

        with col2:
            # Accept both PDF and DOCX
            resume_file = st.file_uploader(
                "Upload Resume (PDF or DOCX)",
                type=["pdf", "docx"]
            )
            if resume_file:
                ext = resume_file.name.split(".")[-1].upper()
                st.caption(f"📄 Uploaded: `{resume_file.name}` ({ext})")

        job_description = st.text_area(
            "Job Description",
            height=280,
            placeholder="Paste the full job description here..."
        )

        submitted = st.form_submit_button("🔍 Analyze Candidate", use_container_width=True)

    if submitted:
        if not candidate_name or not applied_role or not resume_file or not job_description:
            st.error("Please fill in all fields and upload a resume (PDF or DOCX).")
            return

        with st.spinner("🤖 AI is analyzing the candidate... This may take 30-60 seconds."):
            try:
                files = {
                    "resume_file": (
                        resume_file.name,
                        resume_file.getvalue(),
                        "application/pdf" if resume_file.name.endswith(".pdf")
                        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                }
                form_data = {
                    "candidate_name": candidate_name,
                    "applied_role": applied_role,
                    "department": department,
                    "job_description": job_description
                }
                response = httpx.post(
                    f"{BACKEND_URL}/recruitment/analyze",
                    data=form_data,
                    files=files,
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
        st.subheader("📊 Screening Results")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Overall Score", f"{result['overall_score']:.1f} / 10")
        with m2:
            st.metric("Skill Score", f"{result['skill_score']:.1f} / 10")
        with m3:
            rec_display = RECOMMENDATION_EMOJI.get(result["recommendation"], result["recommendation"])
            st.metric("Recommendation", rec_display)

        st.info(f"**Reasoning:** {result['reasoning']}")

        col_match, col_gap = st.columns(2)
        with col_match:
            st.markdown("#### ✅ Matched Skills")
            if result["matched_skills"]:
                for skill in result["matched_skills"]:
                    st.markdown(f"- {skill}")
            else:
                st.markdown("_No matched skills found._")

        with col_gap:
            st.markdown("#### ⚠️ Skill Gaps")
            if result["missing_skills"]:
                for skill in result["missing_skills"]:
                    st.markdown(f"- {skill}")
            else:
                st.markdown("_No skill gaps identified._")

        if result.get("interview_questions"):
            st.markdown("---")
            st.subheader("🎤 Interview Questions")
            for i, q in enumerate(result["interview_questions"], 1):
                q_type = q.get("type", "general").upper()
                st.markdown(f"**{i}. [{q_type}]** {q['question']}")