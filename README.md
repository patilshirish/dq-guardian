# 🛡️ Data Quality Guardian

**An agentic AI multi-agent system for data quality monitoring — built to demonstrate how AI reasoning and human governance combine in enterprise data operations.**

> Built by [Shirish Patil](https://linkedin.com/in/shirishpatil) | Data & AI Executive
> 20+ years building enterprise data platforms, governance frameworks (ARB, DAMA/CDMP), and MDM programs

---

## Why This Exists

Most data quality tooling stops at detection: a threshold is crossed, an alert fires. The harder — and more valuable — work is what happens next: diagnosing *why* the issue occurred, prescribing *what to do about it*, and ensuring a human stays accountable for the decision.

This project is a working proof-of-concept of that fuller workflow, applied to employee data — a domain where data quality failures (a corrupted tenure field, a duplicated record, an invalid satisfaction score) can directly distort attrition models and workforce decisions.

It's deliberately scoped as a **proof-of-concept**, not a production system — built to demonstrate architecture, reasoning quality, and governance design, not to be deployed as-is.

---

## Architecture

```
IBM HR Attrition Dataset
        │
        ▼
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ 1. Ingestion    │───▶│ 2. Profiling   │───▶│ 3. Anomaly      │
│   (deterministic)│   │  (deterministic)│   │   Detection     │
└────────────────┘    └────────────────┘    └───────┬─────────┘
                                                      │
                ┌─────────────────────────────────────┘
                ▼
      ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
      │ 4. Root Cause    │─▶│ 5. Remediation   │─▶│ 6. Report        │
      │   (Claude LLM)   │  │   Advisor (Claude)│  │   Generator      │
      └──────────────────┘  └──────────────────┘  └────────┬─────────┘
                                                              │
                                                              ▼
                                                  ┌──────────────────────┐
                                                  │ 7. Human Review      │
                                                  │ APPROVE / REJECT /   │
                                                  │ ESCALATE             │
                                                  └──────────────────────┘
```

| # | Agent | Type | Responsibility |
|---|-------|------|-----------------|
| 1 | **Data Ingestion** | Deterministic | Load dataset, infer schema, inject realistic DQ issues for demonstration |
| 2 | **Profiling** | Deterministic | Completeness, uniqueness, distribution statistics |
| 3 | **Anomaly Detection** | Deterministic | Statistical outliers (IQR), domain rule violations, duplicates, severity scoring |
| 4 | **Root Cause Reasoning** | LLM (Claude) | Reasons in plain language about *why* each anomaly pattern likely exists |
| 5 | **Remediation Advisor** | LLM (Claude) | Prescribes prioritized, actionable fixes with code and governance steps |
| 6 | **Report Generator** | LLM (Claude) | Synthesizes everything into an executive-readable markdown report |
| 7 | **Human Review** | Human-in-the-loop | Approve / Reject (re-run) / Escalate — conditional routing in the graph |

**Design principle:** deterministic computation (steps 1–3) is fast, cheap, and exact — no LLM needed. Claude is used only where language-based reasoning adds real value (steps 4–6). The human stays the final decision-maker (step 7) — this is not a "set and forget" automation; it's a tool that compresses the distance between a data problem and a *governed* decision.

---

## 🌐 Live Demo

Try it in your browser — no installation needed:

**→ [dq-guardian-patilshirish.streamlit.app](https://dq-guardian-patilshirish.streamlit.app)**

You'll need a free Anthropic API key to run the analysis:
1. Go to **console.anthropic.com** and sign up
2. Create an API key (takes 2 minutes)
3. Paste it in the app sidebar
4. Upload any HR CSV or use the built-in IBM HR sample

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Run the pipeline
python pipeline.py
```

The pipeline will: load the dataset, profile it, detect anomalies, call Claude three times (root cause → remediation → report), then pause and ask you to Approve / Reject / Escalate. The final report is saved to `output/dq_report.md`.

If the HuggingFace dataset load fails (network restrictions, renamed repo), see `get_dataset.py` for a one-time local CSV fallback — no code changes required.

---

## Dataset & Transparency Note

**Source:** IBM HR Analytics Employee Attrition & Performance — a public, fictional dataset (1,470 employees × 35 attributes) created by IBM data scientists, widely used in HR analytics research.

**Important:** the original dataset ships with **zero missing values** — it was built clean for ML tutorials. To make this a meaningful data-quality demonstration, the Ingestion agent deliberately injects a documented set of realistic issues:

| Issue Type | Where | Why It's Realistic |
|---|---|---|
| Missing values | `MonthlyIncome`, `YearsAtCompany` | Mirrors optional fields skipped during onboarding data entry |
| Duplicate records | 20 rows | Mirrors a re-sync from a second HRIS source without dedup logic |
| Invalid categorical codes | `Education`, `EnvironmentSatisfaction` | Mirrors enum drift after a system migration |
| Impossible values | `Age` (150+), `DistanceFromHome` (negative) | Mirrors unit errors and corrupted upstream fields |
| Negative tenure | `TotalWorkingYears` | Mirrors a termination-date-before-hire-date integrity failure |

This is disclosed here so the findings are never mistaken for defects in the original public dataset — every issue found is one this pipeline injected for the purpose of the demonstration.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| Reasoning | Claude (Anthropic) via `langchain-anthropic` |
| Data | pandas, numpy, HuggingFace `datasets` |
| Output | Markdown executive report |

---

## Project Structure

```
dq-guardian/
├── pipeline.py              # LangGraph state machine & entry point
├── get_dataset.py           # One-time local dataset fallback helper
├── requirements.txt
├── README.md
├── agents/
│   ├── ingestion.py         # Node 1
│   ├── profiling.py         # Node 2
│   ├── anomaly.py           # Node 3
│   ├── root_cause.py        # Node 4 (Claude)
│   ├── remediation.py       # Node 5 (Claude)
│   ├── report.py            # Node 6 (Claude)
│   └── human_review.py      # Node 7
└── output/
    └── dq_report.md         # Generated report (gitignored)
```

---

## The Governance Principle This Demonstrates

The Human Review gate is the architectural choice I care most about in this build. Automated pipelines should **surface decisions, not silently make them.** A data quality "fix" applied without human review and accountability is how organizations create a different — and often less visible — kind of data integrity problem.

This mirrors the same principle behind every enterprise governance framework I've built: AI and automation accelerate diagnosis and remediation planning, but a named, accountable human signs off on action. That's the difference between a tool that looks impressive in a demo and one an enterprise can actually trust at scale.

---

## Author

**Shirish Patil** — Data & AI Executive
20+ years in enterprise data architecture, governance (ARB, DAMA/CDMP), MDM/Golden Record programs, and AI/ML — including production systems processing 500,000+ unstructured records with full auditability and human-in-the-loop review.

[LinkedIn](https://linkedin.com/in/shirishpatil)

## License

MIT — free to use, adapt, and build upon with attribution.
