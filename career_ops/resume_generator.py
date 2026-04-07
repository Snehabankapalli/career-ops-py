"""PDF resume generator using Jinja2 and WeasyPrint."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS


class ResumeGenerator:
    """Generates ATS-optimized PDF resumes tailored to job descriptions."""

    def __init__(self, template_dir: str = "templates", output_dir: str = "output"):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True,
        )

    def _extract_keywords(self, job_description: str) -> list[str]:
        """Extract key technical skills from job description."""
        # Common data engineering keywords
        tech_keywords = [
            "python", "sql", "spark", "pyspark", "aws", "snowflake", "kafka",
            "airflow", "dbt", "terraform", "docker", "kubernetes", "gcp",
            "azure", "hadoop", "hive", "presto", "trino", "looker", "tableau",
            "pandas", "numpy", "scipy", "scikit-learn", "tensorflow", "pytorch",
            "mlflow", "kubeflow", "great expectations", "soda", "postgresql",
            "mysql", "mongodb", "redis", "elasticsearch", "kinesis", "lambda",
            "glue", "emr", "s3", "redshift", "bigquery", "data lake", "data warehouse",
            "etl", "elt", "streaming", "batch", "real-time", "ci/cd",
        ]

        found = []
        jd_lower = job_description.lower()
        for keyword in tech_keywords:
            if keyword in jd_lower:
                found.append(keyword)

        return found

    def _tailor_resume_content(
        self,
        cv_content: dict,
        job_description: str,
        keywords: list[str],
    ) -> dict:
        """Adjust resume content to highlight relevant skills."""
        tailored = cv_content.copy()

        # Update skills section to prioritize JD keywords
        if "skills" in tailored:
            existing_skills = [s.lower() for s in tailored["skills"]]
            new_skills = []

            # Add matching keywords first
            for kw in keywords:
                if kw not in existing_skills:
                    new_skills.append(kw.title() if len(kw) > 3 else kw.upper())

            # Add existing skills
            new_skills.extend(tailored["skills"])
            tailored["skills"] = new_skills[:15]  # Keep top 15

        # Customize summary with keywords
        if "summary" in tailored:
            summary = tailored["summary"]
            # Mention top 3 keywords in summary if not already present
            top_keywords = keywords[:3]
            for kw in top_keywords:
                if kw.lower() not in summary.lower():
                    summary += f" Experience with {kw}."
            tailored["summary"] = summary

        return tailored

    def create_tailored_resume(
        self,
        cv_content: dict,
        job_description: str,
        company: str,
        role: str,
        output_filename: Optional[str] = None,
    ) -> str:
        """Generate a tailored PDF resume."""

        # Extract and apply keywords
        keywords = self._extract_keywords(job_description)
        tailored_content = self._tailor_resume_content(cv_content, job_description, keywords)

        # Generate filename
        if not output_filename:
            company_slug = re.sub(r'[^\w\s-]', '', company).strip().lower().replace(" ", "-")
            role_slug = re.sub(r'[^\w\s-]', '', role).strip().lower().replace(" ", "-")[:30]
            output_filename = f"resume-{company_slug}-{role_slug}-{datetime.now().strftime('%Y%m%d')}.pdf"

        output_path = self.output_dir / output_filename

        # Render HTML
        template = self.env.get_template("resume_template.html")
        html_content = template.render(
            **tailored_content,
            keywords=keywords,
            generation_date=datetime.now().strftime("%B %Y"),
        )

        # Convert to PDF
        HTML(string=html_content).write_pdf(str(output_path))

        return str(output_path)

    def create_base_resume(self, cv_content: dict) -> str:
        """Create a base (non-tailored) resume."""
        output_filename = f"resume-base-{datetime.now().strftime('%Y%m%d')}.pdf"
        output_path = self.output_dir / output_filename

        template = self.env.get_template("resume_template.html")
        html_content = template.render(
            **cv_content,
            keywords=[],
            generation_date=datetime.now().strftime("%B %Y"),
        )

        HTML(string=html_content).write_pdf(str(output_path))
        return str(output_path)
