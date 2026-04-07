"""AI-powered offer analysis using Claude API."""

import json
from dataclasses import dataclass, asdict
from typing import Optional

import anthropic

from .scraper import JobData


@dataclass
class EvaluationCriteria:
    """Individual criterion score."""
    name: str
    score: float  # 0-5
    weight: float  # 0-1
    notes: str


@dataclass
class OfferEvaluation:
    """Complete offer evaluation result."""
    job_url: str
    company: str
    role: str
    overall_score: float  # 0-5
    grade: str  # A-F
    criteria: list[EvaluationCriteria]
    recommendation: str  # "strong_apply", "apply", "consider", "skip"
    reasoning: str
    gaps: list[str]
    strengths: list[str]
    interview_prep: dict  # STAR stories suggested


class OfferAnalyzer:
    """Analyzes job offers using Claude API."""

    CRITERIA_DIMENSIONS = [
        "role_match",
        "company_quality",
        "growth_potential",
        "compensation_fit",
        "tech_stack",
        "team_culture",
        "work_life_balance",
        "location_flexibility",
        "mission_alignment",
        "career_trajectory",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def _calculate_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 4.5:
            return "A"
        elif score >= 4.0:
            return "A-"
        elif score >= 3.5:
            return "B+"
        elif score >= 3.0:
            return "B"
        elif score >= 2.5:
            return "B-"
        elif score >= 2.0:
            return "C+"
        elif score >= 1.5:
            return "C"
        else:
            return "D"

    def _get_recommendation(self, score: float, grade: str) -> str:
        """Generate recommendation based on score."""
        if score >= 4.2:
            return "strong_apply"
        elif score >= 3.5:
            return "apply"
        elif score >= 2.5:
            return "consider"
        else:
            return "skip"

    def analyze(
        self,
        job: JobData,
        cv_text: str,
        profile_config: dict,
    ) -> OfferEvaluation:
        """Analyze a job offer against candidate profile."""

        system_prompt = """You are an expert career coach and technical recruiter specializing in data engineering roles.
Your task is to evaluate job opportunities against a candidate's profile objectively and thoroughly.

Evaluate based on these 10 dimensions (each scored 0-5):
1. Role Match - How well does the role align with the candidate's target roles?
2. Company Quality - Company reputation, stability, growth stage
3. Growth Potential - Learning opportunities, career advancement
4. Compensation Fit - Alignment with candidate's target range
5. Tech Stack - Modernity, relevance to candidate's expertise
6. Team Culture - Evidence of good engineering culture
7. Work-Life Balance - Policies, expectations, flexibility
8. Location Flexibility - Remote options, relocation requirements
9. Mission Alignment - Company mission alignment with candidate values
10. Career Trajectory - Strategic fit for long-term career goals

Respond ONLY with a JSON object matching this structure:
{
    "criteria": [
        {"name": "role_match", "score": 4.5, "weight": 0.15, "notes": "..."}
    ],
    "reasoning": "detailed explanation",
    "gaps": ["gap1", "gap2"],
    "strengths": ["strength1", "strength2"],
    "interview_prep": {
        "star_stories": ["story1", "story2"],
        "questions_to_ask": ["q1", "q2"]
    }
}"""

        user_prompt = f"""Evaluate this job opportunity for the candidate.

CANDIDATE PROFILE:
{json.dumps(profile_config, indent=2)}

CANDIDATE CV:
{cv_text[:5000]}...

JOB POSTING:
Company: {job.company}
Title: {job.title}
Location: {job.location or "Not specified"}

Description:
{job.description[:8000]}

Provide your evaluation as JSON."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract JSON from response
            content = response.content[0].text

            # Find JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            result = json.loads(json_str.strip())

            # Calculate weighted score
            criteria_list = [
                EvaluationCriteria(
                    name=c["name"],
                    score=c["score"],
                    weight=c.get("weight", 0.1),
                    notes=c["notes"],
                )
                for c in result.get("criteria", [])
            ]

            weighted_score = sum(c.score * c.weight for c in criteria_list)
            grade = self._calculate_grade(weighted_score)
            recommendation = self._get_recommendation(weighted_score, grade)

            return OfferEvaluation(
                job_url=job.url,
                company=job.company,
                role=job.title,
                overall_score=round(weighted_score, 2),
                grade=grade,
                criteria=criteria_list,
                recommendation=recommendation,
                reasoning=result.get("reasoning", ""),
                gaps=result.get("gaps", []),
                strengths=result.get("strengths", []),
                interview_prep=result.get("interview_prep", {}),
            )

        except Exception as e:
            # Fallback evaluation on error
            return OfferEvaluation(
                job_url=job.url,
                company=job.company,
                role=job.title,
                overall_score=0.0,
                grade="F",
                criteria=[],
                recommendation="skip",
                reasoning=f"Error during analysis: {str(e)}",
                gaps=["Unable to analyze"],
                strengths=[],
                interview_prep={},
            )

    def batch_analyze(
        self,
        jobs: list[JobData],
        cv_text: str,
        profile_config: dict,
    ) -> list[OfferEvaluation]:
        """Analyze multiple jobs."""
        return [self.analyze(job, cv_text, profile_config) for job in jobs]
