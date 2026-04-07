# Career-Ops Python Demo

## Quick Demo (Terminal Recording)

### Step 1: Evaluate a Job

```bash
$ python -m career_ops.cli evaluate https://boards.greenhouse.io/anthropic/jobs/12345

🔍 Evaluating: https://boards.greenhouse.io/anthropic/jobs/12345

Company: Anthropic
Role: Senior Data Engineer

╭──────────────────────────────── Evaluation Results ────────────────────────────────╮
│ Metric            Value                                                            │
│ ──────────────────────────────────────────────────────────                         │
│ Score             4.3/5                                                            │
│ Grade             A-                                                                 │
│ Recommendation    Strong Apply                                                     │
│ Application ID    12                                                               │
╰────────────────────────────────────────────────────────────────────────────────────╯

Reasoning:
Strong alignment with candidate's expertise in AWS serverless architectures
and real-time streaming. Role requires PySpark and Kafka experience which
candidate has 7+ years in. Compensation range ($180K-240K) aligns with target.
Company culture emphasizes AI safety and production reliability - matches
candidate's fintech background.

📄 PDF saved: output/resume-anthropic-senior-data-engineer-20250407.pdf
✅ Tracked in database (ID: 12)
```

### Step 2: View Pipeline Stats

```bash
$ python -m career_ops.cli stats

╭────────────────────── Pipeline Statistics ───────────────────────╮
│ Metric               Value                                       │
│ ──────────────────────────────────────────────────────────────── │
│ Total Applications   47                                          │
│ Strong Apply         12                                          │
│ Average Score        3.8/5                                       │
│ Response Rate        32%                                         │
╰──────────────────────────────────────────────────────────────────╯

Status Breakdown:
  Evaluated: 23
  Applied: 15
  Interview: 6
  Offer: 2
  Rejected: 1
```

### Step 3: Launch Dashboard

```bash
$ python -m career_ops.cli dashboard

🚀 Launching Streamlit dashboard...

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

**Dashboard shows:**
- Pipeline statistics cards
- Score distribution chart
- Application table with filters
- Status update controls

### Step 4: Batch Processing

```bash
$ python -m career_ops.cli batch jobs.txt --parallel 5

🚀 Batch evaluating 8 jobs (max 5 concurrent)

╭──────────────────────────────── Batch Results (8/8 successful) ───────────────────────╮
│ Company            Role                         Score  Grade  Recommendation          │
│ ───────────────────────────────────────────────────────────────────────────────────  │
│ Anthropic          Senior Data Engineer         4.3    A-     Strong Apply            │
│ OpenAI             Data Platform Engineer     4.1    A-     Strong Apply            │
│ Snowflake          Staff Analytics Engineer   3.9    B+     Apply                   │
│ Databricks         Solutions Architect        3.5    B      Apply                   │
│ dbt Labs           Analytics Engineer         3.2    B      Consider                │
│ Fivetran           Senior Data Engineer       2.8    B-     Consider                │
│ Stitch             Data Engineer              2.3    C+     Skip                    │
│ Tiny Startup       Data Scientist             1.8    C      Skip                    │
╰────────────────────────────────────────────────────────────────────────────────────╯
```

## Dashboard Preview

```
┌─────────────────────────────────────────────────────────────────┐
│  💼 Career-Ops                                    [Dashboard]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Total    │  │ Strong   │  │ Avg      │  │ Response │        │
│  │   47     │  │   12     │  │  3.8/5   │  │   32%    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                 │
│  Pipeline Status                                                │
│  ████████████████████████████████████████████                   │
│  Evaluated ████████████████████ 23                              │
│  Applied   ██████████████ 15                                    │
│  Interview ██████ 6                                             │
│  Offer     ██ 2                                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ID │ Company      │ Role              │ Score │ Status  │   │
│  │  12 │ Anthropic    │ Senior Data Eng   │  4.3  │ Applied │   │
│  │  11 │ OpenAI       │ Data Platform Eng │  4.1  │ Applied │   │
│  │  10 │ Snowflake    │ Staff Analytics   │  3.9  │ Interview│  │
│  │  ... │ ...         │ ...               │  ...  │ ...     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture Diagram

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
