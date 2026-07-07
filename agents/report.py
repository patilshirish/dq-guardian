"""
Agent 6 — Report Generator (LLM)
Uses Claude to synthesize all upstream agent outputs into a polished,
executive-ready Data Quality report.
"""

import json
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage


SYSTEM_PROMPT = """You are a Data Governance executive who writes clear, \
authoritative data quality reports for both technical and business audiences \
in an HR / People Analytics context.

Tell a coherent story: What was found -> Why it happened -> What to do -> \
What to watch next. Write with executive precision. Use markdown tables, \
headers, and code sections where useful."""


def generate_report(state: dict, llm) -> dict:
    print("📝 [6/7] Generating executive DQ report (Claude) ...")

    profile     = state.get("profile", {})
    anomalies   = state.get("anomalies", {})
    root_cause  = state.get("root_cause", "")
    remediation = state.get("remediation", "")
    errors      = state.get("errors", [])
    run_ts      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary = anomalies.get("summary", {})

    context = f"""
PIPELINE RUN: {run_ts}
DATASET: IBM HR Analytics Employee Attrition & Performance
ROWS: {profile.get('row_count', 'N/A')} | COLUMNS: {profile.get('column_count', 'N/A')}

ANOMALY SUMMARY:
- Total Issues Detected: {summary.get('total_issues_detected', 0)}
- Severity: {summary.get('severity', 'UNKNOWN')}
- Columns with Nulls: {summary.get('columns_with_missing', 0)}
- Columns with Outliers: {summary.get('columns_with_iqr_outliers', 0)}
- Domain Violations: {summary.get('columns_with_domain_violations', 0)}
- Duplicate Rows: {summary.get('duplicate_rows', 0)}

MISSING VALUE DETAILS:
{json.dumps(anomalies.get('missing_values', {}), indent=2)}

DOMAIN VIOLATIONS:
{json.dumps(anomalies.get('domain_violations', {}), indent=2)}

ROOT CAUSE ANALYSIS:
{root_cause}

REMEDIATION PLAN:
{remediation}

PIPELINE ERRORS: {errors if errors else 'None'}
"""

    prompt = f"""Generate a complete, professional Data Quality Monitoring \
Report using the following pipeline output. The audience is data engineers, \
HR analytics teams, and data governance executives (CDO/VP level).

{context}

Structure the report with EXACTLY these sections and table formats:

1. **Executive Summary** — a table with EXACTLY these 4 columns:
   | Metric | Value | Status | Impact |
   Rows must include: Report Date, Dataset, Total Issues Detected, 
   Issue Density, Data Usability. Do not remove or rename any column.

2. **Data Quality Scorecard** — a table with EXACTLY these 5 columns:
   | Dimension | Score | Status | Trend | Notes |
   Rows: Completeness, Validity, Uniqueness, Consistency, Timeliness, Overall Quality.

3. **Anomaly Findings** — organized by category (Missing Values, Domain 
   Violations, Duplicates) with severity badges and row counts.

4. **Root Cause Analysis** — synthesized from the analysis above, 
   with confidence levels (High / Medium / Low) for each hypothesis.

5. **Remediation Roadmap** — a table with EXACTLY these 5 columns:
   | Action | Owner | Priority | Effort | Timeline |

6. **Risk to Downstream Consumers** — specific impact on attrition 
   models, HR dashboards, and workforce planning reports.

7. **Recommended Monitoring Rules** — as Great Expectations style pseudocode.

8. **Next Steps & Owners** — clear action items with named owners.

IMPORTANT RULES:
- Always use exactly the column names specified above
- Never remove, rename, or merge any columns
- Use markdown tables for all structured data
- Keep business language throughout — avoid overly technical jargon
- Every table must have a header row and at least one data row

Include a header with run metadata. Format cleanly in markdown."""

    try:
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        header = f"""---
# 🛡️ Data Quality Guardian — Executive Report
**Pipeline:** Agentic AI Multi-Agent System (LangGraph + Claude)
**Author:** Shirish Patil | Data & AI Executive
**Run Timestamp:** {run_ts}
**Dataset:** IBM HR Analytics Employee Attrition & Performance
**Architecture:** 7-Node Multi-Agent Pipeline with Human-in-the-Loop Governance
---

"""
        state["report"] = header + response.content
        print("   ✓ Executive report generated")

    except Exception as e:
        state["errors"].append(f"Report LLM error: {str(e)}")
        state["report"] = f"# Data Quality Report\n\nReport generation failed: {str(e)}"
        print(f"   ✗ Report generation error: {e}")

    return state
