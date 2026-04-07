"""Tests for Career-Ops pipeline."""

import pytest
from pathlib import Path
import tempfile

from career_ops.tracker import ApplicationTracker, ApplicationStatus
from career_ops.resume_generator import ResumeGenerator


class TestApplicationTracker:
    """Test suite for application tracker."""

    def test_add_application(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            tracker = ApplicationTracker(db_path=str(db_path))

            app_id = tracker.add_application(
                company="Test Corp",
                role="Data Engineer",
                job_url="https://example.com/job",
                score=4.5,
                grade="A",
                recommendation="strong_apply",
            )

            assert app_id > 0

            app = tracker.get_application(app_id)
            assert app.company == "Test Corp"
            assert app.role == "Data Engineer"
            assert app.score == 4.5

    def test_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            tracker = ApplicationTracker(db_path=str(db_path))

            app_id1 = tracker.add_application(
                company="Test Corp",
                role="Data Engineer",
                job_url="https://example.com/job",
            )

            app_id2 = tracker.add_application(
                company="Test Corp",
                role="Data Engineer",
                job_url="https://example.com/job2",
            )

            # Should return existing ID for duplicate
            assert app_id1 == app_id2

    def test_update_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            tracker = ApplicationTracker(db_path=str(db_path))

            app_id = tracker.add_application(
                company="Test Corp",
                role="Data Engineer",
                job_url="https://example.com/job",
            )

            tracker.update_status(app_id, ApplicationStatus.APPLIED, "Applied via LinkedIn")

            app = tracker.get_application(app_id)
            assert app.status == "Applied"
            assert "LinkedIn" in app.notes

    def test_get_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            tracker = ApplicationTracker(db_path=str(db_path))

            tracker.add_application(
                company="Corp A",
                role="Engineer",
                job_url="https://a.com",
                score=4.5,
                recommendation="strong_apply",
            )
            tracker.add_application(
                company="Corp B",
                role="Senior Engineer",
                job_url="https://b.com",
                score=3.5,
                recommendation="apply",
            )

            stats = tracker.get_stats()
            assert stats.total == 2
            assert stats.average_score == 4.0
            assert stats.strong_apply_count == 1


class TestResumeGenerator:
    """Test suite for resume generator."""

    def test_extract_keywords(self):
        generator = ResumeGenerator(template_dir="templates", output_dir="output")

        jd = "We need Python, Spark, and AWS experience. Kafka is a plus."
        keywords = generator._extract_keywords(jd)

        assert "python" in keywords
        assert "spark" in keywords
        assert "aws" in keywords
        assert "kafka" in keywords

    def test_tailor_resume_content(self):
        generator = ResumeGenerator(template_dir="templates", output_dir="output")

        cv = {
            "skills": ["Python", "SQL"],
            "summary": "Data engineer with 5 years experience.",
        }
        jd = "Looking for Python and Kafka experts."
        keywords = ["python", "kafka"]

        tailored = generator._tailor_resume_content(cv, jd, keywords)

        assert "Kafka".title() in tailored["skills"]
        assert "python" in tailored["summary"].lower()
