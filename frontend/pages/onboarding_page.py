import streamlit as st
import httpx
import os

BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

EMPLOYEES = {
    "Arjun Mehta": {
        "id": 1,
        "role": "Senior SDE",
        "dept": "software_engineering",
        "mgr": "Rohit Verma",
    },
    "Priya Sharma": {
        "id": 2,
        "role": "SDE II",
        "dept": "software_engineering",
        "mgr": "Rohit Verma",
    },
    "Suresh Reddy": {
        "id": 5,
        "role": "Ops Manager",
        "dept": "operations",
        "mgr": "Director Ops",
    },
    "Kavita Nair": {
        "id": 6,
        "role": "Process Analyst",
        "dept": "operations",
        "mgr": "Suresh Reddy",
    },
    "Sunita Joshi": {
        "id": 8,
        "role": "Account Executive",
        "dept": "sales",
        "mgr": "Vijay Patel",
    },
    "Vijay Patel": {
        "id": 9,
        "role": "Sales Manager",
        "dept": "sales",
        "mgr": "VP Sales",
    },
}


def render():
    st.header("📋 Onboarding Plan Generator")

    mode = st.radio(
        "How do you want to proceed?",
        ["Choose from existing employees", "Enter new employee manually"],
        horizontal=True,
    )

    st.divider()

    if mode == "Choose from existing employees":
        with st.form("onb_existing"):
            emp_label = st.selectbox("Select Employee", list(EMPLOYEES.keys()))
            submitted = st.form_submit_button(
                "Generate Onboarding Plan", type="primary", use_container_width=True
            )

        if submitted:
            emp = EMPLOYEES[emp_label]
            payload = {
                "employee_id": emp["id"],
                "employee_name": emp_label,
                "role": emp["role"],
                "department": emp["dept"],
                "manager_name": emp["mgr"],
            }
            _run_and_display(payload)

    else:
        with st.form("onb_manual"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", placeholder="e.g. Ravi Kumar")
                role = st.text_input("Role / Title", placeholder="e.g. Data Analyst")
            with col2:
                dept = st.selectbox(
                    "Department", ["software_engineering", "operations", "sales"]
                )
                manager = st.text_input("Manager Name", placeholder="e.g. Suresh Reddy")

            submitted = st.form_submit_button(
                "Generate Onboarding Plan", type="primary", use_container_width=True
            )

        if submitted:
            if not all([name.strip(), role.strip(), manager.strip()]):
                st.warning("Please fill in Name, Role, and Manager Name.")
                return

            payload = {
                "employee_id": 0,  # 0 = not a seeded employee
                "employee_name": name.strip(),
                "role": role.strip(),
                "department": dept,
                "manager_name": manager.strip(),
            }
            _run_and_display(payload)


def _run_and_display(payload: dict):
    with st.spinner(
        f"Generating onboarding plan for {payload['employee_name']}... (~30–40s)"
    ):
        try:
            response = httpx.post(
                f"{BACKEND}/onboarding/generate", json=payload, timeout=120
            )
            response.raise_for_status()
            r = response.json()
        except httpx.HTTPError as e:
            st.error(f"Backend error: {e}")
            return

    st.success(
        f"Onboarding plan ready for **{payload['employee_name']}** ({payload['role']})"
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "✅ 30-Day Checklist",
            "📚 Training Roadmap",
            "🛠 Tools Access",
            "📅 First Week",
        ]
    )

    with tab1:
        st.subheader("30-Day Onboarding Checklist")
        for item in r.get("checklist", []):
            st.write(
                f"**Day {item.get('day', '?')}** · "
                f"`{item.get('category', '')}` · "
                f"_{item.get('owner', '')}_ — {item.get('task', '')}"
            )

    with tab2:
        st.subheader("90-Day Training Roadmap")
        for item in r.get("training_roadmap", []):
            st.write(
                f"**Week {item.get('week', '?')}** · `{item.get('type', '')}` — {item.get('topic', '')}"
            )
            st.caption(f"Outcome: {item.get('outcome', '')}")

    with tab3:
        st.subheader("Tools & System Access")
        for item in r.get("tools_access", []):
            badge = "🔴" if item.get("priority") == "high" else "🟡"
            st.write(f"{badge} **{item.get('tool', '')}** — {item.get('purpose', '')}")

    with tab4:
        st.subheader("First Week Schedule")
        for day in r.get("first_week", []):
            st.markdown(f"**{day.get('day', '')}**")
            for act in day.get("activities", []):
                st.write(
                    f"  {act.get('time', '')} · {act.get('activity', '')} "
                    f"_(with {act.get('with_whom', 'team')})_"
                )
