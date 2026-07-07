"""
Agent 7 — Human Review Gate
Presents findings to a human reviewer who can APPROVE, REJECT
(re-run the pipeline), or ESCALATE to data governance leadership.
This is the governance control that keeps a human accountable for
any decision with real business consequence.
"""


def human_review_node(state: dict) -> dict:
    print("\n" + "=" * 64)
    print("  👤 [7/7] HUMAN REVIEW REQUIRED")
    print("=" * 64)

    summary = state.get("anomalies", {}).get("summary", {})

    print(f"\n  Severity      : {summary.get('severity', 'UNKNOWN')}")
    print(f"  Total Issues  : {summary.get('total_issues_detected', 0)}")
    print(f"  Duplicates    : {summary.get('duplicate_rows', 0)}")
    print(f"  Domain Errors : {summary.get('columns_with_domain_violations', 0)} columns")
    print(f"  Null Columns  : {summary.get('columns_with_missing', 0)}")

    print("\n  Full report saved to → output/dq_report.md")
    print("\n  Review Options:")
    print("  [A] APPROVE  — Accept findings, mark pipeline run complete")
    print("  [R] REJECT   — Re-run pipeline from the start")
    print("  [E] ESCALATE — Flag for Data Governance / CDO review")
    print()

    decision_map = {"a": "APPROVE", "r": "REJECT", "e": "ESCALATE"}

    try:
        choice = input("  Enter decision [A/R/E]: ").strip().lower()
        decision = decision_map.get(choice, "APPROVE")
    except (EOFError, KeyboardInterrupt):
        decision = "APPROVE"
        print("  (Non-interactive mode: defaulting to APPROVE)")

    notes = ""
    if decision != "APPROVE":
        try:
            notes = input("  Add reviewer notes (optional): ").strip()
        except (EOFError, KeyboardInterrupt):
            notes = ""

    state["human_decision"] = decision
    state["human_notes"] = notes

    print(f"\n  ✅ Decision recorded: {decision}")
    if notes:
        print(f"  📌 Notes: {notes}")
    print("=" * 64 + "\n")

    return state
