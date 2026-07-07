"""
Data Quality Guardian — Agentic AI Multi-Agent System
Author: Shirish Patil | Data & AI Executive
Architecture: Multi-Agent LangGraph + Claude (Anthropic)
Dataset: IBM HR Analytics Employee Attrition & Performance
"""

import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic

from agents.ingestion import ingest_data
from agents.profiling import profile_data
from agents.anomaly import detect_anomalies
from agents.root_cause import analyze_root_cause
from agents.remediation import advise_remediation
from agents.report import generate_report
from agents.human_review import human_review_node


# ── State schema ──────────────────────────────────────────────────────────
# This is the shared "memory" that flows through every node in the graph.
# Each agent reads what it needs and writes its own output back into state.

class DQState(TypedDict):
    raw_data:       object   # pandas DataFrame
    profile:        dict     # statistical profile from Profiling Agent
    anomalies:      dict     # anomaly findings from Anomaly Detection Agent
    root_cause:     str      # Claude's root cause narrative
    remediation:    str      # Claude's remediation plan
    report:         str      # Claude's final executive report (markdown)
    human_decision: str      # APPROVE | REJECT | ESCALATE
    human_notes:    str      # reviewer's free-text notes
    errors:         list     # any errors logged along the way


# ── LLM client (shared by the 3 reasoning agents) ───────────────────────
# Using Haiku for cost-efficient iteration. Swap to a stronger model
# (e.g. claude-opus-4-5) for your final "official" run before publishing.

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0.2,
    max_tokens=2048,
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)


# ── Build the graph ───────────────────────────────────────────────────────

def build_pipeline():
    graph = StateGraph(DQState)

    graph.add_node("ingest",       lambda s: ingest_data(s))
    graph.add_node("profile",      lambda s: profile_data(s))
    graph.add_node("anomaly",      lambda s: detect_anomalies(s))
    graph.add_node("root_cause",   lambda s: analyze_root_cause(s, llm))
    graph.add_node("remediation",  lambda s: advise_remediation(s, llm))
    graph.add_node("report",       lambda s: generate_report(s, llm))
    graph.add_node("human_review", lambda s: human_review_node(s))

    graph.set_entry_point("ingest")

    # Guard: skip Claude calls entirely if ingestion failed
    graph.add_conditional_edges(
        "ingest",
        lambda s: "skip" if s.get("raw_data") is None or s.get("errors") else "continue",
        {"continue": "profile", "skip": "human_review"}
    )
    graph.add_edge("profile",     "anomaly")
    graph.add_edge("anomaly",     "root_cause")
    graph.add_edge("root_cause",  "remediation")
    graph.add_edge("remediation", "report")
    graph.add_edge("report",      "human_review")

    # Conditional routing based on the human's decision
    graph.add_conditional_edges(
        "human_review",
        lambda s: s.get("human_decision", "APPROVE"),
        {
            "APPROVE":  END,
            "REJECT":   "ingest",   # re-run the entire pipeline from scratch
            "ESCALATE": END,        # exit; caller / human handles escalation
        }
    )

    return graph.compile()


# ── Entry point ───────────────────────────────────────────────────────────

def run_pipeline():
    pipeline = build_pipeline()

    initial_state: DQState = {
        "raw_data":       None,
        "profile":        {},
        "anomalies":      {},
        "root_cause":     "",
        "remediation":    "",
        "report":         "",
        "human_decision": "",
        "human_notes":    "",
        "errors":         [],
    }

    print("\n" + "=" * 64)
    print("  DATA QUALITY GUARDIAN")
    print("  Agentic AI Multi-Agent Data Quality Pipeline")
    print("  LangGraph + Claude (Anthropic) | IBM HR Attrition Dataset")
    print("=" * 64 + "\n")

    final_state = pipeline.invoke(initial_state)

    os.makedirs("output", exist_ok=True)
    report_path = "output/dq_report.md"
    with open(report_path, "w") as f:
        f.write(final_state.get("report", "No report generated."))

    print(f"\n✅ Pipeline complete. Report saved → {report_path}")
    print(f"   Human Decision : {final_state.get('human_decision')}")
    print(f"   Reviewer Notes : {final_state.get('human_notes') or 'None'}\n")

    return final_state


if __name__ == "__main__":
    run_pipeline()
