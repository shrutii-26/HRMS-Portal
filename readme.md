# 🏢 HRMS AI Portal

An AI-powered Human Resource Management System built with **LangGraph**, **Groq**, **FastAPI**, and **Streamlit**. Three intelligent agent modules handle recruitment screening, employee onboarding, and performance reviews — each backed by a proper multi-step workflow rather than a single prompt.

---

## ✨ Features

| Module                          | What it does                                                                                                                |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 🎯 **Recruitment Agent**        | Parses resumes, extracts skills, scores candidates against JDs, generates interview questions, gives hiring recommendation  |
| 📋 **Onboarding Agent**         | Generates department-specific 30-day checklists, 90-day training roadmaps, tools access lists, and first-week schedules     |
| 📊 **Performance Review Agent** | Computes weighted scores, analyzes strengths and growth areas, writes a narrative summary, gives tier-aware recommendations |

---

## 🧱 Tech Stack

```
Streamlit      →  frontend UI (port 8501)
FastAPI        →  thin backend API (port 8000)
LangGraph      →  multi-step agent workflows
LangChain      →  LLM integration + structured outputs
Groq           →  free-tier LLM (llama-3.3-70b-versatile)
SQLAlchemy     →  ORM
SQLite         →  local database (hrms.db)
Pydantic       →  structured output schemas
PyMuPDF        →  PDF resume parsing
httpx          →  Streamlit → FastAPI communication
```

---

## 📁 Project Structure

```
hrms_portal/
│
├── backend/
│   ├── main.py                  # FastAPI app — 3 POST endpoints
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── recruitment.py       # LangGraph graph (4 nodes, conditional branch)
│   │   ├── onboarding.py        # LangGraph graph (5 nodes, linear)
│   │   └── performance.py       # LangGraph graph (5 nodes, math-first)
│   └── db/
│       ├── __init__.py
│       ├── database.py          # Engine, session factory, init_db
│       └── models.py            # 4 SQLAlchemy tables
│
├── frontend/
│   ├── app.py                   # Streamlit entry point + sidebar nav
│   └── _pages/                  # Underscore prevents Streamlit auto-discovery
│       ├── __init__.py
│       ├── recruitment_page.py
│       ├── onboarding_page.py   # Supports both seeded + manual employee input
│       └── performance_page.py
│
├── seed_data.py                 # One-time script — inserts 10 sample employees
├── .env                         # API keys and config (never commit this)
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd hrms_portal

python -m venv venv

# Windows
.\venv\Scripts\Activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the `hrms_portal/` directory:

```env
GROQ_API_KEY=gsk_your_key_here
BACKEND_URL=http://localhost:8000
```

Get your free Groq API key at [console.groq.com](https://console.groq.com).

### 4. Seed the database

```bash
python seed_data.py
```

This creates `hrms.db` and inserts 10 sample employees across 3 departments.

### 5. Run the backend

```bash
# Terminal 1
uvicorn backend.main:app --reload --port 8000
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Run the frontend

```bash
# Terminal 2 (activate venv first if needed)
streamlit run frontend/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🔁 LangGraph Workflows

### Recruitment Agent

```
extract_skills → score_candidate ──┬─(≥7.0)─→ gen_interview_questions ─┐
                                   └─(<7.0)─────────────────────────────┤
                                                                         ▼
                                                             hiring_recommendation
```

- **4 Groq calls** per run (~20–30s)
- Conditional branch: candidates scoring ≥ 7.0 get interview questions generated; others skip directly to the recommendation

### Onboarding Agent

```
load_dept_context → gen_checklist → gen_training_roadmap → gen_tools_access → gen_first_week
```

- **4 Groq calls** per run (~30–40s)
- First node is pure data (no LLM) — injects department context into state
- Supports both seeded employees and manually entered new hires

### Performance Review Agent

```
compute_weighted_score → analyze_strengths → analyze_weaknesses → gen_summary → gen_recommendations
```

- **4 Groq calls** per run (~30s)
- First node is pure Python math (no LLM) — KPI × 0.40 + tasks × 0.40 + attendance × 0.20
- Rating tier (`exceptional` / `meets_expectations` / `needs_improvement`) flows through state and shapes all downstream prompts

---

## 🗄️ Database Schema

| Table                 | Key columns                                                                                                     |
| --------------------- | --------------------------------------------------------------------------------------------------------------- |
| `employees`           | id, name, department, role, status                                                                              |
| `candidates`          | id, name, applied_role, overall_score, recommendation, matched_skills, missing_skills, interview_questions      |
| `onboarding_plans`    | id, employee_id, checklist, training_roadmap, tools_access, first_week                                          |
| `performance_reviews` | id, employee_id, review_period, weighted_score, overall_rating, strengths, weaknesses, summary, recommendations |

List-type fields (skills, questions, checklist items) are stored as JSON strings.

---

## 👥 Sample Employees

| #   | Name         | Role               | Department           |
| --- | ------------ | ------------------ | -------------------- |
| 1   | Arjun Mehta  | Senior SDE         | Software Engineering |
| 2   | Priya Sharma | SDE II             | Software Engineering |
| 3   | Rohit Verma  | DevOps Engineer    | Software Engineering |
| 4   | Neha Gupta   | Frontend Developer | Software Engineering |
| 5   | Suresh Reddy | Ops Manager        | Operations           |
| 6   | Kavita Nair  | Process Analyst    | Operations           |
| 7   | Amit Singh   | Logistics Lead     | Operations           |
| 8   | Sunita Joshi | Account Executive  | Sales                |
| 9   | Vijay Patel  | Sales Manager      | Sales                |
| 10  | Anjali Das   | Business Dev Rep   | Sales                |

---

## ⚡ Groq Free Tier Notes

- **Model:** `llama-3.3-70b-versatile`
- **Rate limit:** ~30 requests/minute
- **Calls per workflow:** 4 Groq calls = 4 of those 30 requests
- **Fallback:** Switch to `llama-3.1-8b-instant` in each agent file if you hit rate limits — faster, slightly less precise on structured output
- **JSON reliability:** If any node returns malformed JSON, add `model_kwargs={"response_format": {"type": "json_object"}}` to the `ChatGroq()` constructor in that agent file

---

## 🛠️ API Endpoints

| Method | Endpoint               | Description                                  |
| ------ | ---------------------- | -------------------------------------------- |
| `POST` | `/recruitment/analyze` | Analyze a candidate — form data + PDF upload |
| `POST` | `/onboarding/generate` | Generate onboarding plan — JSON body         |
| `POST` | `/performance/review`  | Generate performance review — JSON body      |
| `GET`  | `/health`              | Health check                                 |
| `GET`  | `/docs`                | Auto-generated Swagger UI                    |

---

## 📋 Requirements

```
fastapi==0.111.0
uvicorn==0.30.1
streamlit==1.35.0
langgraph==0.1.19
langchain==0.2.6
langchain-groq==0.1.6
langchain-core==0.2.11
sqlalchemy==2.0.31
PyMuPDF==1.24.5
httpx==0.27.0
pydantic==2.7.4
python-dotenv==1.0.1
python-multipart==0.0.9
```

---

## 🔮 Roadmap / Possible Enhancements

- [ ] Add authentication (simple JWT or Streamlit login)
- [ ] Export onboarding plans and performance reviews as PDF
- [ ] Add a candidate pipeline view showing all past recruitment runs
- [ ] Switch to Claude Opus via Anthropic API for higher output quality
- [ ] Add email notifications when a review or plan is generated
- [ ] Deploy backend to Railway / Render and frontend to Streamlit Cloud

---

## 📄 License

MIT — free to use, modify, and build on.
