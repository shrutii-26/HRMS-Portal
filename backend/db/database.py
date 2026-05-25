# SQLAlchemy engine, session factory, and DB initialization
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./hrms.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def init_db():
    """Create all tables if they don't exist."""
    from backend.db.models import Employee, Candidate, OnboardingPlan, PerformanceReview  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """Yield a DB session and ensure it closes after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
