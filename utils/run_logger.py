"""
utils/run_logger.py
Persists every pipeline run to a JSON log file so findings can be
tracked across executions — enabling trend analysis and drift detection.
This is what separates a one-time script from a monitoring system.
"""

import json
import os
from datetime import datetime

LOG_FILE = "output/run_history.json"


def load_run_history() -> list:
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_run(state: dict) -> dict:
    """Extract key metrics from state and append to run history."""
    os.makedirs("output", exist_ok=True)
    history = load_run_history()

    summary = state.get("anomalies", {}).get("summary", {})

    run_entry = {
        "run_id":        len(history) + 1,
        "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_issues":  summary.get("total_issues_detected", 0),
        "severity":      summary.get("severity", "UNKNOWN"),
        "duplicates":    summary.get("duplicate_rows", 0),
        "null_columns":  summary.get("columns_with_missing", 0),
        "domain_errors": summary.get("columns_with_domain_violations", 0),
        "decision":      state.get("human_decision", "UNKNOWN"),
        "notes":         state.get("human_notes", ""),
        "errors":        state.get("errors", []),
    }

    history.append(run_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(history, f, indent=2)

    return run_entry


def print_run_summary(history: list):
    """Print a trend summary across all runs."""
    if not history:
        return

    print("\n" + "=" * 64)
    print("  📈 RUN HISTORY — Data Quality Trend")
    print("=" * 64)
    print(f"  {'Run':<5} {'Timestamp':<22} {'Issues':<8} {'Severity':<10} {'Decision'}")
    print("  " + "-" * 58)
    for r in history[-10:]:  # show last 10 runs
        print(f"  {r['run_id']:<5} {r['timestamp']:<22} "
              f"{r['total_issues']:<8} {r['severity']:<10} {r['decision']}")

    # Trend detection
    if len(history) >= 2:
        last  = history[-1]["total_issues"]
        prev  = history[-2]["total_issues"]
        delta = last - prev
        trend = "📈 WORSE" if delta > 0 else "📉 BETTER" if delta < 0 else "➡ STABLE"
        print(f"\n  Trend vs previous run: {trend} ({delta:+d} issues)")

    print("=" * 64 + "\n")
