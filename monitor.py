"""
monitor.py — Continuous Monitoring Mode
Runs the Data Quality Guardian pipeline on a schedule, persisting
findings across runs so quality trends can be tracked over time.

This is what separates a one-time script from an always-on monitoring
system — the same architectural pattern used in enterprise data
observability platforms.

USAGE:
    # Run every 60 seconds (demo mode — shows the "always on" concept)
    python monitor.py --interval 60

    # Run every hour (realistic for a daily HR data feed)
    python monitor.py --interval 3600

    # Run once immediately (same as python pipeline.py but with logging)
    python monitor.py --interval 0

    # Run non-interactively (no human review prompt — for scheduling)
    python monitor.py --interval 60 --auto-approve
"""

import argparse
import time
import os
from datetime import datetime

from pipeline import build_pipeline
from utils.run_logger import save_run, load_run_history, print_run_summary


# ── Auto-approve patch for unattended runs ────────────────────────────────
# When running on a schedule, we can't wait for human input.
# In auto-approve mode, we log findings and send an alert instead.

def _auto_review_node(state: dict) -> dict:
    """Non-interactive human review — auto-approves and logs for alerting."""
    summary = state.get("anomalies", {}).get("summary", {})
    severity = summary.get("severity", "UNKNOWN")

    # In a real system this would trigger a Slack/Teams/PagerDuty alert
    if severity == "HIGH":
        print(f"   🚨 AUTO-ESCALATE: Severity HIGH — "
              f"{summary.get('total_issues_detected', 0)} issues detected")
        print(f"   📧 [SIMULATED] Alert sent to Data Governance team")
        state["human_decision"] = "ESCALATE"
    else:
        print(f"   ✅ AUTO-APPROVE: Severity {severity} — within acceptable threshold")
        state["human_decision"] = "APPROVE"

    state["human_notes"] = f"Auto-processed at {datetime.now().strftime('%H:%M:%S')}"
    return state


def run_once(auto_approve: bool = False) -> dict:
    """Run the full pipeline once and return final state."""
    from langgraph.graph import StateGraph, END
    from pipeline import DQState, llm
    from agents.ingestion import ingest_data
    from agents.profiling import profile_data
    from agents.anomaly import detect_anomalies
    from agents.root_cause import analyze_root_cause
    from agents.remediation import advise_remediation
    from agents.report import generate_report
    from agents.human_review import human_review_node

    graph = StateGraph(DQState)

    review_node = _auto_review_node if auto_approve else human_review_node

    graph.add_node("ingest",       lambda s: ingest_data(s))
    graph.add_node("profile",      lambda s: profile_data(s))
    graph.add_node("anomaly",      lambda s: detect_anomalies(s))
    graph.add_node("root_cause",   lambda s: analyze_root_cause(s, llm))
    graph.add_node("remediation",  lambda s: advise_remediation(s, llm))
    graph.add_node("report",       lambda s: generate_report(s, llm))
    graph.add_node("human_review", lambda s: review_node(s))

    graph.set_entry_point("ingest")

    graph.add_conditional_edges(
        "ingest",
        lambda s: "skip" if s.get("raw_data") is None else "continue",
        {"continue": "profile", "skip": "human_review"}
    )
    graph.add_edge("profile",     "anomaly")
    graph.add_edge("anomaly",     "root_cause")
    graph.add_edge("root_cause",  "remediation")
    graph.add_edge("remediation", "report")
    graph.add_edge("report",      "human_review")

    graph.add_conditional_edges(
        "human_review",
        lambda s: s.get("human_decision", "APPROVE"),
        {"APPROVE": END, "REJECT": "ingest", "ESCALATE": END}
    )

    pipeline = graph.compile()

    initial_state: DQState = {
        "raw_data": None, "profile": {}, "anomalies": {},
        "root_cause": "", "remediation": "", "report": "",
        "human_decision": "", "human_notes": "", "errors": [],
    }

    return pipeline.invoke(initial_state)


def run_continuous(interval_seconds: int, auto_approve: bool):
    """Run the pipeline repeatedly on a schedule."""
    run_number = 0

    print("\n" + "=" * 64)
    print("  🛡️  DATA QUALITY GUARDIAN — CONTINUOUS MONITORING MODE")
    print(f"  Schedule: every {interval_seconds}s | "
          f"Mode: {'Auto-Approve' if auto_approve else 'Interactive'}")
    print("  Press Ctrl+C to stop")
    print("=" * 64)

    try:
        while True:
            run_number += 1
            print(f"\n{'─' * 64}")
            print(f"  🔄 Starting Run #{run_number} — "
                  f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'─' * 64}\n")

            # Run the pipeline
            final_state = run_once(auto_approve=auto_approve)

            # Save run to history log
            run_entry = save_run(final_state)

            # Save timestamped report
            os.makedirs("output/reports", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"output/reports/dq_report_run{run_number}_{ts}.md"
            with open(report_path, "w") as f:
                f.write(final_state.get("report", ""))
            print(f"  📄 Report saved → {report_path}")

            # Show trend across all runs
            history = load_run_history()
            print_run_summary(history)

            if interval_seconds == 0:
                print("  Single run complete (--interval 0). Exiting.")
                break

            print(f"  ⏱  Next run in {interval_seconds}s — "
                  f"press Ctrl+C to stop\n")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n\n  🛑 Monitoring stopped by user.")
        history = load_run_history()
        if history:
            print_run_summary(history)
        print("  Run history saved → output/run_history.json\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Data Quality Guardian — Continuous Monitoring Mode"
    )
    parser.add_argument(
        "--interval", type=int, default=0,
        help="Seconds between runs (0 = run once, 60 = every minute)"
    )
    parser.add_argument(
        "--auto-approve", action="store_true",
        help="Skip human review prompt (for unattended/scheduled runs)"
    )
    args = parser.parse_args()

    run_continuous(
        interval_seconds=args.interval,
        auto_approve=args.auto_approve
    )
