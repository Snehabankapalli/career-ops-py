"""Main pipeline orchestrating job evaluation workflow."""

import asyncio
import os
from pathlib import Path
from typing import Optional

import yaml

from .scraper import JobScraper, JobData
from .analyzer import OfferAnalyzer, OfferEvaluation
from .resume_generator import ResumeGenerator
from .tracker import ApplicationTracker, ApplicationStatus


class Pipeline:
    """Main orchestration class for job evaluation pipeline."""

    def __init__(
        self,
        config_path: str = "config/profile.yml",
        cv_path: str = "config/cv.yml",
        db_path: str = "data/applications.db",
    ):
        self.config_path = config_path
        self.cv_path = cv_path

        # Load configuration
        self.config = self._load_yaml(config_path)
        self.cv_content = self._load_yaml(cv_path) if os.path.exists(cv_path) else {}

        # Initialize components
        self.analyzer = OfferAnalyzer(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.resume_generator = ResumeGenerator()
        self.tracker = ApplicationTracker(db_path=db_path)

    def _load_yaml(self, path: str) -> dict:
        """Load YAML configuration file."""
        with open(path, "r") as f:
            return yaml.safe_load(f)

    async def evaluate_job(
        self,
        job_url: str,
        generate_pdf: bool = True,
    ) -> dict:
        """Full pipeline: scrape → analyze → generate PDF → track."""

        print(f"🔍 Scraping job: {job_url}")

        async with JobScraper(headless=True) as scraper:
            job_data = await scraper.scrape(job_url)

        print(f"📋 Found: {job_data.title} at {job_data.company}")
        print(f"🤖 Analyzing with Claude...")

        # Analyze
        evaluation = self.analyzer.analyze(
            job=job_data,
            cv_text=str(self.cv_content),
            profile_config=self.config,
        )

        print(f"✅ Score: {evaluation.overall_score}/5 (Grade: {evaluation.grade})")
        print(f"📊 Recommendation: {evaluation.recommendation}")

        result = {
            "job": job_data,
            "evaluation": evaluation,
            "pdf_path": None,
            "app_id": None,
        }

        # Generate PDF if score is decent and requested
        if generate_pdf and evaluation.overall_score >= 2.5:
            print(f"📄 Generating tailored resume...")
            pdf_path = self.resume_generator.create_tailored_resume(
                cv_content=self.cv_content,
                job_description=job_data.description,
                company=job_data.company,
                role=job_data.title,
            )
            result["pdf_path"] = pdf_path
            print(f"✅ PDF saved: {pdf_path}")

        # Track in database
        app_id = self.tracker.add_application(
            company=job_data.company,
            role=job_data.title,
            job_url=job_url,
            score=evaluation.overall_score,
            grade=evaluation.grade,
            recommendation=evaluation.recommendation,
            location=job_data.location,
            pdf_path=result.get("pdf_path"),
        )
        result["app_id"] = app_id
        print(f"✅ Tracked in database (ID: {app_id})")

        return result

    async def evaluate_batch(
        self,
        urls: list[str],
        max_concurrent: int = 3,
    ) -> list[dict]:
        """Evaluate multiple jobs with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def eval_with_limit(url: str) -> Optional[dict]:
            async with semaphore:
                try:
                    return await self.evaluate_job(url)
                except Exception as e:
                    print(f"❌ Failed to evaluate {url}: {e}")
                    return None

        tasks = [eval_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    def get_pipeline_stats(self):
        """Get overall pipeline statistics."""
        return self.tracker.get_stats()

    def update_application_status(
        self,
        app_id: int,
        status: ApplicationStatus,
        notes: Optional[str] = None,
    ):
        """Update status of an application."""
        self.tracker.update_status(app_id, status, notes)

    def get_applications(
        self,
        status: Optional[ApplicationStatus] = None,
        min_score: Optional[float] = None,
    ):
        """Get applications with filtering."""
        return self.tracker.get_all_applications(status=status, min_score=min_score)
