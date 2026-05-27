# 🏢 HRMS AI Portal

An AI-powered Human Resource Management System built with **FastAPI**, **Streamlit**, **LangGraph**, and **Groq (LLaMA 3.3 70B)**. The portal automates three core HR workflows — recruitment screening, employee onboarding, and performance reviews — using multi-step LangGraph agent pipelines.

🔗 **Live Demo:** https://hrms-app-shruti.streamlit.app/  

---

## ✨ Features

### 🎯 Recruitment Screening
- Upload a candidate resume as **PDF or DOCX**
- AI validates the document is actually a resume (rejects lecture notes, invoices, random files)
- Extracts skills and years of experience
- Scores the candidate against the job description
- Generates targeted interview questions for high-scoring candidates
- Provides a final hiring recommendation: `Strong Yes / Yes / Maybe / No`

### 📋 Onboarding Plan Generator
- Select an existing employee or enter a new one manually
- Generates a **30-day onboarding checklist** with task owners and categories
- Produces a **90-day training roadmap** with weekly milestones
- Lists all **tools and system access** needed with priorities (Day 1 / Week 1 / Month 1)
- Designs a structured **first week schedule** (5 days)

### 📊 Performance Review Generator
- Input attendance, KPI, and task completion scores
- Add manager feedback, peer feedback, and self-assessment
- Live weighted score preview with tier classification
- AI generates strengths, growth areas, a professional summary, and SMART recommendations

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| AI Orchestration | LangGraph |
| LLM | Groq — LLaMA 3.3 70B Versatile |
| Database | SQLite + SQLAlchemy ORM |
| PDF Parsing | PyMuPDF (fitz) |
| DOCX Parsing | python-docx |
| HTTP Client | httpx |
| Deployment (Backend) | Render |
| Deployment (Frontend) | Streamlit Cloud |

---

## 🗂 Project Structure

```
HRMS-Portal/
├── backend/
│   ├── agents/
│   │   ├── recruitment.py      # LangGraph recruitment pipeline
│   │   ├── onboarding.py       # LangGraph onboarding pipeline
│   │   └── performance.py      # LangGraph performance review pipeline
│   ├── db/
│   │   ├── database.py         # SQLAlchemy engine and session
│   │   └── models.py           # ORM table definitions
│   └── main.py                 # FastAPI app with 3 POST endpoints
├── frontend/
│   ├── pages/
│   │   ├── recruitment_page.py
│   │   ├── onboarding_page.py
│   │   └── performance_page.py
│   ├── app.py                  # Streamlit entry point
│   └── requirements.txt        # Frontend dependencies
├── requirements                # Backend dependencies
├── seed_data.py                # Sample employee data seeder
└── .env                        # Environment variables (not committed)
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.10+
- A [Groq API key](https://console.groq.com)

### 1. Clone the repo
```bash
git clone https://github.com/shrutii-26/HRMS-Portal.git
cd HRMS-Portal
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements
```

### 4. Create your `.env` file
```
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run the backend (Terminal 1)
```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Run the frontend (Terminal 2)
```bash
cd frontend
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/recruitment/analyze` | Analyze a candidate resume |
| POST | `/onboarding/generate` | Generate an onboarding plan |
| POST | `/performance/review` | Generate a performance review |

Interactive API docs available at `/docs` (Swagger UI).

---

## 🧠 LangGraph Agent Architecture

Each HR workflow is a **LangGraph StateGraph** — a directed pipeline where each node performs one focused task and passes results to the next.

**Recruitment Pipeline:**
```
extract_skills → score_candidate → [gen_interview_questions*] → hiring_recommendation
                                   *only if score >= 7.0
```

**Onboarding Pipeline:**
```
load_dept_context → gen_checklist → gen_training_roadmap → gen_tools_access → gen_first_week
```

**Performance Pipeline:**
```
compute_weighted_score → analyze_strengths → analyze_weaknesses → gen_summary → gen_recommendations
```

---

## 🚀 Future Scope

- **Persistent Database Migration** — Currently using SQLite which resets on every Render redeploy due to ephemeral file storage. The planned migration is to PostgreSQL (via Render Postgres or Supabase). Since the entire data layer is abstracted through SQLAlchemy ORM, this requires changing a single connection string in `database.py` and adding `psycopg2-binary` to dependencies — making it a trivial switch when moving to production.

- **Authentication & Role-Based Access** — Add JWT-based auth so HR managers, employees, and admins see different views and data.

- **Email Notifications** — Auto-send onboarding plans and review summaries to employees via email.

- **Dashboard & Analytics** — Visualize hiring trends, performance distributions, and onboarding completion rates.

- **Multi-tenant Support** — Allow multiple organizations to use the portal with isolated data.

- **Resume Parsing Improvements** — Support scanned PDF resumes using OCR (e.g. Tesseract) for image-based documents.

---

## 👩‍💻 Author

**Shruti Suman** — [github.com/shrutii-26](https://github.com/shrutii-26)
