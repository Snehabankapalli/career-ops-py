"""Career-Ops Python - AI-powered job search automation for data engineers."""

from .pipeline import Pipeline
from .scraper import JobScraper
from .analyzer import OfferAnalyzer
from .resume_generator import ResumeGenerator
from .tracker import ApplicationTracker

__version__ = "1.0.0"
__author__ = "Sneha Bankapalli"
__email__ = "snehabankapalli@gmail.com"

__all__ = [
    "Pipeline",
    "JobScraper",
    "OfferAnalyzer",
    "ResumeGenerator",
    "ApplicationTracker",
]
