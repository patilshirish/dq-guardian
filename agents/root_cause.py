"""
Agent 4 — Root Cause Reasoning (LLM)
Uses Claude to reason about WHY the detected anomalies exist,
connecting symptoms to plausible upstream HRIS/payroll pipeline causes.
"""

import json
from langchain_core.messages import HumanMessage, SystemMessage


SYSTEM_PROMPT = """You are a Senior Data Quality Engineer specializing in HR \
and payroll data systems (HRIS, ATS, payroll integrations).

Your task is to analyze data quality anomalies in employee data and reason \
about their most likely root causes with precision and business context. \
Think like an investigator connecting symptoms (anomalies) to upstream causes \
(source systems, integration points, manual data entry, system migrations).

Structure your response as:
1. A brief executive summary (2-3 sentences)
2. Root cause analysis per anomaly category, with a confidence level \
   (High / Medium / Low) for each hypothesis
3. A ranked list of the most probable upstream causes overall
4. Risk to HR/People Analytics decisions if left unresolved (e.g. attrition \
   models, compensation analysis, workforce planning)

Be specific and grounded in how real HRIS data pipelines actually fail. \
Avoid generic statements."""


def analyze_root_cause(state: dict, llm) -> dict:
    print("🧠 [4/7] Reasoning about root causes (Claude) ...")

    anomalies = state.get("anomalies", {})
    profile = state.get("profile", {})

    if not anomalies:
        state["root_cause"] = "No anomalies to analyze."
        return state

    context = {
        "dataset": "IBM HR Analytics Employee Attrition & Performance",
        "rows": profile.get("row_count"),
        "columns": profile.get("column_count"),
        "summary": anomalies.get("summary", {}),
        "missing_values": anomalies.get("missing_values", {}),
        "iqr_outliers": anomalies.get("iqr_outliers", {}),
        "domain_violations": anomalies.get("domain_violations", {}),
        "duplicates": anomalies.get("duplicates", {}),
    }

    prompt = f"""Analyze the following data quality anomaly report for an \
employee attrition dataset used in HR analytics and workforce planning.

ANOMALY REPORT:
{json.dumps(context, indent=2)}

Provide a thorough root-cause analysis. For each anomaly category, explain \
WHY it's likely present (not just what it is) and WHICH upstream system or \
process most likely introduced it. Conclude with the business risk if \
these issues feed into attrition prediction models or HR dashboards \
without remediation.

Format as structured markdown with headers."""

    try:
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        state["root_cause"] = response.content
        print("   ✓ Root cause analysis complete")
    except Exception as e:
        state["errors"].append(f"Root cause LLM error: {str(e)}")
        state["root_cause"] = f"Root cause analysis failed: {str(e)}"
        print(f"   ✗ Root cause error: {e}")

    return state
