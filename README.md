# Career-Ops Python

> AI-powered job search automation for data engineers. Built with Python, Playwright, and Streamlit.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=flat&logo=playwright&logoColor=white)](https://playwright.dev)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude](https://img.shields.io/badge/Claude_API-D97757?style=flat&logo=anthropic&logoColor=white)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

![Demo](docs/demo.gif)

## Overview

**Career-Ops Python** is a production-ready job search automation system designed specifically for data engineers. It combines web scraping, AI-powered evaluation, and automated resume generation into a single, trackable pipeline.

This project demonstrates:
- **Web scraping at scale** with Playwright (handles JS-rendered job boards)
- **AI integration** using Claude API for intelligent offer evaluation
- **Document generation** using Jinja2 + WeasyPrint for ATS-optimized PDFs
- **Data persistence** with SQLite for application tracking
- **Interactive dashboards** with Streamlit
- **Production patterns** from 7 years of data engineering experience

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAREER-OPS PYTHON                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Scraper    │───▶│   Analyzer   │───▶│    Tracker   │      │
│  │  (Playwright)│    │ (Claude API) │    │   (SQLite)   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Job Boards  │    │   Scoring    │    │  Dashboard   │      │
│  │Greenhouse/etc│    │   A-F Grade  │    │  (Streamlit) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                            │                                     │
│                            ▼                                     │
│                     ┌──────────────┐                             │
│                     │ PDF Generator│                             │
│                     │(Jinja2+PDF)  │                             │
│                     └──────────────┘                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Smart Scraping** | Extracts JDs from Greenhouse, Lever, Ashby, and company pages using Playwright |
| **AI Evaluation** | Scores opportunities A-F across 10 dimensions using Claude API |
| **ATS PDFs** | Generates tailored resumes with keyword injection for each application |
| **Application Tracker** | SQLite-backed pipeline with status management |
| **Streamlit Dashboard** | Visual pipeline browser, filtering, and analytics |
| **Batch Processing** | Evaluate multiple URLs in parallel |
| **Interview Prep** | Auto-generates STAR stories based on your experience |

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/Snehabankapalli/career-ops-py.git
cd career-ops-py
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure
cp config/profile.example.yml config/profile.yml
# Edit config/profile.yml with your details

# Set your Claude API key
export ANTHROPIC_API_KEY="your-api-key"

# Run the dashboard
streamlit run dashboard/app.py

# Or use CLI
python -m career_ops.cli --help
```

---

## Usage

### Evaluate a Single Job

```python
from career_ops import Pipeline

pipeline = Pipeline()
result = pipeline.evaluate_job("https://boards.greenhouse.io/company/jobs/12345")
print(f"Score: {result.score}/5")
print(f"Recommendation: {result.recommendation}")
```

### Generate Tailored Resume

```python
from career_ops import ResumeGenerator

generator = ResumeGenerator()
pdf_path = generator.create_tailored_resume(
    job_url="https://...",
    output_path="output/resume_company.pdf"
)
```

### Batch Processing

```bash
python -m career_ops.batch --urls urls.txt --parallel 5
```

---

## Project Structure

```
career-ops-py/
├── career_ops/              # Main package
│   ├── __init__.py
│   ├── scraper.py          # Playwright job scraper
│   ├── analyzer.py         # Claude API integration
│   ├── resume_generator.py # PDF generation
│   ├── tracker.py          # SQLite database layer
│   └── pipeline.py         # Orchestration
├── dashboard/              # Streamlit app
│   └── app.py
├── config/                 # User configuration
│   ├── profile.example.yml
│   └── archetypes.yml
├── data/                   # SQLite database (gitignored)
├── output/                 # Generated PDFs (gitignored)
├── templates/              # Resume templates
│   └── resume_template.html
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Scraping** | Playwright |
| **AI** | Claude API (Anthropic) |
| **PDF Generation** | Jinja2 + WeasyPrint |
| **Database** | SQLite + SQLAlchemy |
| **Dashboard** | Streamlit |
| **CLI** | Click |
| **Config** | PyYAML |
| **Testing** | pytest |

---

## Why This Exists

I built this because job searching as a senior data engineer is broken:

- **70% of job postings** are poor fits discovered only after lengthy reading
- **Tailoring resumes** for each application takes 30+ minutes
- **Tracking applications** across 50+ companies becomes unmanageable
- **Interview prep** requires organizing scattered notes

This system automates the repetitive parts while keeping humans in control of decisions.

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Connect

- GitHub: [@Snehabankapalli](https://github.com/Snehabankapalli)
- LinkedIn: [linkedin.com/in/sneha2095](https://linkedin.com/in/sneha2095)

---

*Built with 7 years of production data engineering experience. Ships only what I'd use myself.*
