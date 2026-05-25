# ORM table definitions for the 4 HRMS tables
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from backend.db.database import Base


# Stores employee master data
class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, default="active")


# Stores recruitment screening results
class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    applied_role = Column(String, nullable=False)
    department = Column(String, nullable=False)
    overall_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    recommendation = Column(String, default="")
    matched_skills = Column(Text, default="[]")
    missing_skills = Column(Text, default="[]")
    interview_questions = Column(Text, default="[]")
    reasoning = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# Stores generated onboarding plans
class OnboardingPlan(Base):
    __tablename__ = "onboarding_plans"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    checklist = Column(Text, default="[]")
    training_roadmap = Column(Text, default="[]")
    tools_access = Column(Text, default="[]")
    first_week = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)


# Stores AI-generated performance reviews
class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    review_period = Column(String, nullable=False)
    weighted_score = Column(Float, default=0.0)
    overall_rating = Column(String, default="")
    strengths = Column(Text, default="[]")
    weaknesses = Column(Text, default="[]")
    summary = Column(Text, default="")
    recommendations = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
