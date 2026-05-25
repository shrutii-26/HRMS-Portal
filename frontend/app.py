# Streamlit entry point — sidebar navigation across 3 HR modules
import streamlit as st

st.set_page_config(page_title="HRMS AI Portal", page_icon="🏢", layout="wide")

# Sidebar navigation
st.sidebar.title("🏢 HRMS AI Portal")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate to",
    ["🎯 Recruitment", "📋 Onboarding", "📊 Performance Review"],
    index=0
)

# Route to the selected page
if page == "🎯 Recruitment":
    from pages.recruitment_page import render
    render()
elif page == "📋 Onboarding":
    from pages.onboarding_page import render
    render()
elif page == "📊 Performance Review":
    from pages.performance_page import render
    render()
