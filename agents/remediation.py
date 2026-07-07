"""
Agent 5 — Remediation Advisor (LLM)
Uses Claude to prescribe concrete, prioritized remediation actions,
sized for an HR data governance audience.
"""

import json
from langchain_core.messages import HumanMessage, SystemMessage


SYSTEM_PROMPT = """You are a Chief Data Officer advising on HR data quality \
remediation strategy. You think across three horizons:
- Immediate fixes (data patching / filtering for current analysis)
- Pipeline fixes (validation rules in the HRIS integration layer)
- Governance fixes (ownership, SLAs, monitoring, data stewardship)

For each issue category, provide:
- Priority (P1 Critical / P2 High / P3 Medium)
- Effort estimate (Hours / Days / Weeks)
- A short Python/pandas snippet where applicable
- A validation check to confirm the fix worked

Be prescriptive and specific to HR/People Analytics data. Avoid vague advice."""


def advise_remediation(state: dict, llm) -> dict:
    print("🔧 [5/7] Generating remediation advice (Claude) ...")

    anomalies = state.get("anomalies", {})
    root_cause = state.get("root_cause", "")

    if not anomalies:
        state["remediation"] = "No issues to remediate."
        return state

    context = {
        "anomaly_summary":    anomalies.get("summary", {}),
        "missing_columns":    list(anomalies.get("missing_values", {}).keys()),
        "outlier_columns":    list(anomalies.get("iqr_outliers", {}).keys()),
        "domain_violations":  list(anomalies.get("domain_violations", {}).keys()),
        "duplicate_count":    anomalies.get("duplicates", {}).get("count", 0),
        "severity":           anomalies.get("summary", {}).get("severity", "UNKNOWN"),
        "root_cause_summary": (root_cause[:800] + "...") if len(root_cause) > 800 else root_cause,
    }

    prompt = f"""Based on the following data quality issues and root cause \
analysis for the IBM HR Attrition dataset, prescribe a complete remediation plan.

CONTEXT:
{json.dumps(context, indent=2)}

For each issue category, provide:
1. **Immediate Action** (with a pandas snippet)
2. **Pipeline Fix** (HRIS integration / ETL layer)
3. **Governance Action** (ownership, alerting, SLA)
4. **Priority & Effort**
5. **Validation Check**

Close with an overall remediation roadmap and sequencing.
Format as structured markdown."""

    try:
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        state["remediation"] = response.content
        print("   ✓ Remediation plan generated")
    except Exception as e:
        state["errors"].append(f"Remediation LLM error: {str(e)}")
        state["remediation"] = f"Remediation advice failed: {str(e)}"
        print(f"   ✗ Remediation error: {e}")

    return state
