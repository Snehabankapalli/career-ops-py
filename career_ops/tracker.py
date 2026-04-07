"""SQLite-based application tracker."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class ApplicationStatus(str, Enum):
    """Canonical application statuses."""
    EVALUATED = "Evaluated"
    APPLIED = "Applied"
    RESPONDED = "Responded"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"
    DISCARDED = "Discarded"
    SKIP = "Skip"


class ApplicationRecord(Base):
    """Database model for job applications."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Job details
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    job_url = Column(Text, nullable=False)
    location = Column(String(255))
    salary_range = Column(String(255))

    # Evaluation
    score = Column(Float)
    grade = Column(String(10))
    recommendation = Column(String(50))

    # Application tracking
    status = Column(String(50), default=ApplicationStatus.EVALUATED.value)
    applied_date = Column(DateTime)
    notes = Column(Text)

    # File paths
    pdf_path = Column(String(500))
    report_path = Column(String(500))

    def __repr__(self):
        return f"<Application(id={self.id}, company={self.company}, role={self.role}, status={self.status})>"


@dataclass
class ApplicationStats:
    """Dashboard statistics."""
    total: int
    by_status: dict[str, int]
    average_score: float
    strong_apply_count: int
    response_rate: float


class ApplicationTracker:
    """Manages application pipeline in SQLite."""

    def __init__(self, db_path: str = "data/applications.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_application(
        self,
        company: str,
        role: str,
        job_url: str,
        score: Optional[float] = None,
        grade: Optional[str] = None,
        recommendation: Optional[str] = None,
        location: Optional[str] = None,
        salary_range: Optional[str] = None,
        pdf_path: Optional[str] = None,
        report_path: Optional[str] = None,
    ) -> int:
        """Add a new application to the tracker."""
        session = self.Session()
        try:
            # Check for duplicates
            existing = (
                session.query(ApplicationRecord)
                .filter_by(company=company, role=role)
                .first()
            )
            if existing:
                return existing.id

            app = ApplicationRecord(
                company=company,
                role=role,
                job_url=job_url,
                score=score,
                grade=grade,
                recommendation=recommendation,
                location=location,
                salary_range=salary_range,
                pdf_path=pdf_path,
                report_path=report_path,
            )
            session.add(app)
            session.commit()
            return app.id
        finally:
            session.close()

    def update_status(self, app_id: int, status: ApplicationStatus, notes: Optional[str] = None):
        """Update application status."""
        session = self.Session()
        try:
            app = session.query(ApplicationRecord).filter_by(id=app_id).first()
            if app:
                app.status = status.value
                if status == ApplicationStatus.APPLIED:
                    app.applied_date = datetime.utcnow()
                if notes:
                    app.notes = notes
                session.commit()
        finally:
            session.close()

    def get_application(self, app_id: int) -> Optional[ApplicationRecord]:
        """Get single application by ID."""
        session = self.Session()
        try:
            return session.query(ApplicationRecord).filter_by(id=app_id).first()
        finally:
            session.close()

    def get_all_applications(
        self,
        status: Optional[ApplicationStatus] = None,
        min_score: Optional[float] = None,
    ) -> list[ApplicationRecord]:
        """Get applications with optional filtering."""
        session = self.Session()
        try:
            query = session.query(ApplicationRecord)

            if status:
                query = query.filter_by(status=status.value)
            if min_score:
                query = query.filter(ApplicationRecord.score >= min_score)

            return query.order_by(ApplicationRecord.created_at.desc()).all()
        finally:
            session.close()

    def get_stats(self) -> ApplicationStats:
        """Get dashboard statistics."""
        session = self.Session()
        try:
            total = session.query(ApplicationRecord).count()

            by_status = {}
            for status in ApplicationStatus:
                count = session.query(ApplicationRecord).filter_by(status=status.value).count()
                by_status[status.value] = count

            avg_score_result = session.query(ApplicationRecord.score).filter(
                ApplicationRecord.score.isnot(None)
            ).all()
            avg_score = sum(s[0] for s in avg_score_result) / len(avg_score_result) if avg_score_result else 0

            strong_apply = session.query(ApplicationRecord).filter_by(
                recommendation="strong_apply"
            ).count()

            applied = by_status.get(ApplicationStatus.APPLIED.value, 0)
            responded = by_status.get(ApplicationStatus.RESPONDED.value, 0) + \
                       by_status.get(ApplicationStatus.INTERVIEW.value, 0) + \
                       by_status.get(ApplicationStatus.OFFER.value, 0)
            response_rate = (responded / applied * 100) if applied > 0 else 0

            return ApplicationStats(
                total=total,
                by_status=by_status,
                average_score=round(avg_score, 2),
                strong_apply_count=strong_apply,
                response_rate=round(response_rate, 1),
            )
        finally:
            session.close()

    def search(self, query: str) -> list[ApplicationRecord]:
        """Search applications by company or role."""
        session = self.Session()
        try:
            return (
                session.query(ApplicationRecord)
                .filter(
                    (ApplicationRecord.company.ilike(f"%{query}%")) |
                    (ApplicationRecord.role.ilike(f"%{query}%"))
                )
                .all()
            )
        finally:
            session.close()
