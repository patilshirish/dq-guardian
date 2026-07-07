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

Structure the report with these sections:
1. **Executive Summary** (5-6 bullets, business language)
2. **Dataset Overview** (table with key metrics)
3. **Data Quality Scorecard** (table: dimension | score | status)
4. **Anomaly Findings** (by category, with severity)
5. **Root Cause Analysis** (synthesized)
6. **Remediation Roadmap** (table: Action | Owner | Priority | Timeline)
7. **Risk to Downstream Consumers** (attrition models, HR dashboards)
8. **Recommended Monitoring Rules** (as pseudocode)
9. **Next Steps & Owners**

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
