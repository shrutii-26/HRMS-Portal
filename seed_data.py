# Seed script — inserts 10 sample employees across 3 departments
# Run once: python seed_data.py
from backend.db.database import init_db, SessionLocal
from backend.db.models import Employee

EMPLOYEES = [
    {"name": "Arjun Mehta", "department": "Software Engineering", "role": "Senior SDE", "status": "active"},
    {"name": "Priya Sharma", "department": "Software Engineering", "role": "SDE II", "status": "active"},
    {"name": "Rohit Verma", "department": "Software Engineering", "role": "DevOps Engineer", "status": "active"},
    {"name": "Neha Gupta", "department": "Software Engineering", "role": "Frontend Developer", "status": "active"},
    {"name": "Suresh Reddy", "department": "Operations", "role": "Ops Manager", "status": "active"},
    {"name": "Kavita Nair", "department": "Operations", "role": "Process Analyst", "status": "active"},
    {"name": "Amit Singh", "department": "Operations", "role": "Logistics Lead", "status": "active"},
    {"name": "Sunita Joshi", "department": "Sales", "role": "Account Executive", "status": "active"},
    {"name": "Vijay Patel", "department": "Sales", "role": "Sales Manager", "status": "active"},
    {"name": "Anjali Das", "department": "Sales", "role": "Business Dev Rep", "status": "active"},
]


def seed():
    """Initialize DB and insert 10 sample employees if the table is empty."""
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Employee).count()
        if existing > 0:
            print(f"Database already has {existing} employees. Skipping seed.")
            return
        for emp_data in EMPLOYEES:
            db.add(Employee(**emp_data))
        db.commit()
        print(f"Seeded {len(EMPLOYEES)} employees successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
