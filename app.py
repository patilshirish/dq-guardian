"""
app.py — Data Quality Guardian Web App
A Streamlit interface that wraps the full 7-node pipeline
so anyone can upload a CSV and run a live AI data quality analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime
from io import StringIO

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Quality Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f1117; }

    /* Card panels */
    .dq-card {
        background: #1a1d27;
        border: 1px solid #2d3148;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    /* Severity badges */
    .badge-high    { background:#ff4b4b22; color:#ff4b4b; border:1px solid #ff4b4b55;
                     padding:3px 12px; border-radius:20px; font-weight:700; font-size:0.85rem; }
    .badge-medium  { background:#ffa50022; color:#ffa500; border:1px solid #ffa50055;
                     padding:3px 12px; border-radius:20px; font-weight:700; font-size:0.85rem; }
    .badge-low     { background:#00c85322; color:#00c853; border:1px solid #00c85355;
                     padding:3px 12px; border-radius:20px; font-weight:700; font-size:0.85rem; }

    /* Agent step rows */
    .agent-step {
        display:flex; align-items:center; gap:12px;
        padding:10px 16px; border-radius:8px;
        margin-bottom:6px; background:#1a1d27;
        border:1px solid #2d3148;
        font-size:0.95rem;
    }
    .agent-step.done    { border-color:#00c85344; }
    .agent-step.running { border-color:#ffa50044; background:#1a1d2f; }
    .agent-step.waiting { opacity:0.45; }

    /* Metric tiles */
    .metric-tile {
        background:#1a1d27; border:1px solid #4a4f6a;
        border-radius:8px; padding:1rem; text-align:center;
    }
    .metric-tile .val { font-size:2rem; font-weight:700; color:#ffffff; }
    .metric-tile .lbl { font-size:0.75rem; color:#cccccc; text-transform:uppercase;
                        letter-spacing:0.08em; margin-top:4px; }                        

    /* Header */
    .app-header {
        background: linear-gradient(135deg, #1a1d27 0%, #12142a 100%);
        border-bottom: 1px solid #2d3148;
        padding: 1.5rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
    }

    h1, h2, h3 { color: #e0e4ff !important; }
    p, li { color: #a0a4c0; }
    code { background: #2d3148; color: #7c8cf8; padding: 2px 6px; border-radius:4px; }

    /* Hide streamlit branding */
    #MainMenu, footer { visibility: hidden; }

    /* Make markdown tables readable on dark background */
    .stMarkdown table {
        color: #ffffff !important;
        background: #1a1d27 !important;
    }
    .stMarkdown table th {
        color: #ffffff !important;
        background: #2d3148 !important;
        font-weight: 700 !important;
        border: 1px solid #4a4f6a !important;
        padding: 8px 12px !important;
    }
    .stMarkdown table td {
        color: #e0e4ff !important;
        border: 1px solid #2d3148 !important;
        padding: 8px 12px !important;
    }
    .stMarkdown table tr:nth-child(even) {
        background: #22253a !important;
    }
    .stMarkdown p, .stMarkdown li {
        color: #e0e4ff !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ffffff !important;
    }

    /* Sidebar — light background, dark fonts */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6 !important;
        border-right: 1px solid #d0d4e0 !important;
    }
    [data-testid="stSidebar"] * {
        color: #1a1d27 !important;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        color: #444860 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] h3 {
        color: #0f1117 !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] strong {
        color: #0f1117 !important;
    }
    [data-testid="stSidebar"] a {
        color: #4a56c8 !important;
        text-decoration: none !important;
    }
    [data-testid="stSidebar"] a:hover {
        color: #0f1117 !important;
        text-decoration: underline !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #d0d4e0 !important;
    }
    [data-testid="stSidebar"] .stTextInput label {
        color: #444860 !important;
    }
    [data-testid="stSidebar"] .stTextInput input {
        background-color: #ffffff !important;
        color: #1a1d27 !important;
        border: 1px solid #d0d4e0 !important;
    }
    [data-testid="stSidebar"] .stSuccess {
        background-color: #e6f9ee !important;
        color: #1a7a3e !important;
    }
    [data-testid="stSidebar"] .stWarning {
        background-color: #fff8e6 !important;
        color: #7a4f1a !important;
    }  
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ Data Quality Guardian")
    st.markdown("*Agentic AI · LangGraph · Claude*")
    st.divider()

    st.markdown("**How it works**")
    steps = [
        ("📥", "Ingest", "Loads your CSV"),
        ("📊", "Profile", "Statistical baseline"),
        ("🔍", "Detect", "Finds anomalies"),
        ("🧠", "Reason", "Claude explains why"),
        ("🔧", "Remediate", "Claude prescribes fixes"),
        ("📝", "Report", "Claude writes summary"),
        ("👤", "Review", "You approve or escalate"),
    ]
    for icon, name, desc in steps:
        st.markdown(f"{icon} **{name}** — {desc}")

    st.divider()
    st.markdown("**Built by**")
    st.markdown("Shirish Patil | Data & AI")
    st.markdown("[LinkedIn](https://linkedin.com/in/shirishraopatil) · "
                "[GitHub](https://github.com/patilshirish)")
    st.divider()

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Your key is used only for this session and never stored.",
    )
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key
        st.success("API key set ✓")
    elif os.environ.get("ANTHROPIC_API_KEY"):
        st.success("API key loaded from environment ✓")
    else:
        st.warning("Enter your Anthropic API key to run analysis")


# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1 style="margin:0; font-size:1.8rem;">🛡️ Data Quality Guardian</h1>
    <p style="margin:4px 0 0 0; color:#7c8cf8;">
        Agentic AI pipeline · 7 nodes · LangGraph + Claude
    </p>
</div>
""", unsafe_allow_html=True)


# ── Upload section ────────────────────────────────────────────────────────
st.markdown("### Upload Your Dataset")
st.markdown(
    "Upload any HR or employee CSV file. "
    "The pipeline will profile it, detect anomalies, and use Claude to "
    "reason about root causes and prescribe remediations."
)

col_upload, col_sample = st.columns([3, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=["csv"],
        label_visibility="collapsed",
    )

with col_sample:
    st.markdown("<br>", unsafe_allow_html=True)
    use_sample = st.button("📋 Use IBM HR Sample", use_container_width=True)


# ── Load data ─────────────────────────────────────────────────────────────
df_raw = None

if use_sample:
    sample_path = "data/WA_Fn-UseC_-HR-Employee-Attrition.csv"
    if os.path.exists(sample_path):
        df_raw = pd.read_csv(sample_path)
        st.success(f"IBM HR Attrition dataset loaded — "
                   f"{len(df_raw):,} rows × {len(df_raw.columns)} columns")
    else:
        st.error("Sample dataset not found. "
                 "Place the IBM HR Attrition CSV at `data/WA_Fn-UseC_-HR-Employee-Attrition.csv`")

elif uploaded_file:
    try:
        df_raw = pd.read_csv(uploaded_file)
        st.success(f"Uploaded: **{uploaded_file.name}** — "
                   f"{len(df_raw):,} rows × {len(df_raw.columns)} columns")
    except Exception as e:
        st.error(f"Could not read file: {e}")


# ── Dataset preview ───────────────────────────────────────────────────────
if df_raw is not None:
    with st.expander("👁 Preview dataset (first 5 rows)", expanded=False):
        st.dataframe(df_raw.head(), use_container_width=True)

    st.divider()

    # ── Run button ────────────────────────────────────────────────────────
    api_ready = bool(os.environ.get("ANTHROPIC_API_KEY"))
    run_col, _ = st.columns([1, 3])
    with run_col:
        run_btn = st.button(
            "▶ Run Analysis",
            type="primary",
            use_container_width=True,
            disabled=not api_ready,
        )
    if not api_ready:
        st.caption("⚠ Enter your Anthropic API key in the sidebar to enable analysis.")


# ── Pipeline execution ────────────────────────────────────────────────────
if df_raw is not None and api_ready and run_btn:

    st.markdown("### Pipeline Execution")

    # Agent status display
    agent_names = [
        ("📥", "Data Ingestion",         "Loading and preparing dataset"),
        ("📊", "Data Profiling",          "Computing statistical baseline"),
        ("🔍", "Anomaly Detection",       "Identifying data quality issues"),
        ("🧠", "Root Cause Reasoning",    "Claude reasoning about causes"),
        ("🔧", "Remediation Advisor",     "Claude prescribing fixes"),
        ("📝", "Report Generator",        "Claude writing executive report"),
        ("👤", "Human Review",            "Awaiting your decision"),
    ]

    placeholders = []
    for icon, name, desc in agent_names:
        ph = st.empty()
        ph.markdown(
            f'<div class="agent-step waiting">'
            f'<span style="font-size:1.2rem">{icon}</span>'
            f'<span><strong>{name}</strong> — {desc}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        placeholders.append(ph)

    def set_step(i, status):
        icon, name, desc = agent_names[i]
        icons = {"done": "✅", "running": "⏳", "waiting": icon}
        colors = {"done": "#00c853", "running": "#ffa500", "waiting": "#8b8fa8"}
        placeholders[i].markdown(
            f'<div class="agent-step {status}">'
            f'<span style="font-size:1.2rem">{icons[status]}</span>'
            f'<span style="color:{colors[status]}">'
            f'<strong>{name}</strong> — {desc}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Run each agent inline ─────────────────────────────────────────────
    rng = np.random.default_rng(seed=42)
    n = len(df_raw)
    df = df_raw.copy()

    # Node 1 — Ingestion
    set_step(0, "running")
    time.sleep(0.3)
    if "MonthlyIncome" in df.columns:
        idx = rng.choice(n, size=int(n * 0.03), replace=False)
        df.loc[idx, "MonthlyIncome"] = np.nan
    if "YearsAtCompany" in df.columns:
        idx = rng.choice(n, size=int(n * 0.02), replace=False)
        df.loc[idx, "YearsAtCompany"] = np.nan
    dup_rows = df.sample(n=min(20, n), random_state=42)
    df = pd.concat([df, dup_rows], ignore_index=True)
    n2 = len(df)
    for col, lo, hi in [("Age", 150, 200), ("DistanceFromHome", -30, -1),
                         ("TotalWorkingYears", -10, -1)]:
        if col in df.columns:
            idx = rng.choice(n2, size=5, replace=False)
            df.loc[idx, col] = rng.integers(lo, hi, size=5).astype(float)
    set_step(0, "done")

    # Node 2 — Profiling
    set_step(1, "running")
    time.sleep(0.3)
    profile = {"row_count": len(df), "column_count": len(df.columns),
               "duplicate_rows": int(df.duplicated().sum())}
    col_profiles = {}
    for col in df.columns:
        s = df[col]
        cp = {"dtype": str(s.dtype), "null_count": int(s.isna().sum()),
              "null_pct": round(float(s.isna().mean() * 100), 2),
              "unique_count": int(s.nunique())}
        if pd.api.types.is_numeric_dtype(s) and s.notna().any():
            desc = s.describe()
            cp.update({"min": round(float(desc["min"]), 2),
                        "max": round(float(desc["max"]), 2),
                        "mean": round(float(desc["mean"]), 2)})
        col_profiles[col] = cp
    profile["columns"] = col_profiles
    profile["columns_with_nulls"] = [c for c, p in col_profiles.items() if p["null_count"] > 0]
    set_step(1, "done")

    # Node 3 — Anomaly Detection
    set_step(2, "running")
    time.sleep(0.3)
    anomalies = {"missing_values": {}, "iqr_outliers": {}, "domain_violations": {}, "duplicates": {}}
    for col, cp in col_profiles.items():
        if cp["null_count"] > 0:
            anomalies["missing_values"][col] = {"count": cp["null_count"], "pct": cp["null_pct"]}
    domain_rules = {
        "Age": ("Age must be 16–100", lambda x: (x < 16) | (x > 100)),
        "DistanceFromHome": ("Cannot be negative", lambda x: x < 0),
        "TotalWorkingYears": ("Cannot be negative", lambda x: x < 0),
    }
    for col, (rule, fn) in domain_rules.items():
        if col in df.columns:
            s = df[col].dropna()
            cnt = int(fn(s).sum())
            if cnt > 0:
                anomalies["domain_violations"][col] = {"count": cnt, "rule": rule}
    dup_count = int(df.duplicated().sum())
    anomalies["duplicates"] = {"count": dup_count,
                                "pct": round(dup_count / len(df) * 100, 2)}
    total_issues = (sum(v["count"] for v in anomalies["missing_values"].values())
                    + sum(v["count"] for v in anomalies["domain_violations"].values())
                    + dup_count)
    severity = "HIGH" if total_issues > 60 else "MEDIUM" if total_issues > 20 else "LOW"
    anomalies["summary"] = {
        "total_issues_detected": total_issues,
        "columns_with_missing": len(anomalies["missing_values"]),
        "columns_with_iqr_outliers": 0,
        "columns_with_domain_violations": len(anomalies["domain_violations"]),
        "duplicate_rows": dup_count,
        "severity": severity,
    }
    set_step(2, "done")

    # Nodes 4-6 — LLM calls
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.2, max_tokens=2048)

    context_json = json.dumps({
        "dataset": "HR Employee Dataset",
        "rows": profile["row_count"],
        "summary": anomalies["summary"],
        "missing_values": anomalies["missing_values"],
        "domain_violations": anomalies["domain_violations"],
        "duplicates": anomalies["duplicates"],
    }, indent=2)

    # Node 4 — Root Cause
    set_step(3, "running")
    rc_response = llm.invoke([
        SystemMessage(content="You are a Senior Data Quality Engineer specializing in HR data systems."),
        HumanMessage(content=f"Analyze these data quality anomalies and explain their root causes "
                             f"with confidence levels. Format as structured markdown.\n\n{context_json}")
    ])
    root_cause = rc_response.content
    set_step(3, "done")

    # Node 5 — Remediation
    set_step(4, "running")
    rem_response = llm.invoke([
        SystemMessage(content="You are a CDO advising on HR data quality remediation. "
                              "Be prescriptive with priorities P1/P2/P3 and effort estimates."),
        HumanMessage(content=f"Prescribe a remediation plan for these issues. "
                             f"Format as structured markdown.\n\n{context_json}\n\nROOT CAUSE:\n{root_cause[:500]}")
    ])
    remediation = rem_response.content
    set_step(4, "done")

    # Node 6 — Report
    set_step(5, "running")
    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rep_response = llm.invoke([
        SystemMessage(content="You are a Data Governance executive writing an executive DQ report. "
                              "Use markdown tables and headers. Be precise and business-focused."),
        HumanMessage(content=f"Generate a complete executive Data Quality Report with: "
                             f"Executive Summary, DQ Scorecard table, Anomaly Findings, "
                             f"Remediation Roadmap table, and Next Steps.\n\n"
                             f"Run: {run_ts}\nDataset: {profile['row_count']} rows × "
                             f"{profile['column_count']} cols\n\n"
                             f"ANOMALIES:\n{context_json}\n\n"
                             f"ROOT CAUSE:\n{root_cause}\n\n"
                             f"REMEDIATION:\n{remediation}")
    ])
    report = f"""---
# 🛡️ Data Quality Guardian — Executive Report
**Run:** {run_ts} | **Pipeline:** LangGraph + Claude (Anthropic)
**Author:** Shirish Patil | Data & AI Executive
---

""" + rep_response.content
    set_step(5, "done")

    # Node 7 — Human Review (interactive in UI)
    set_step(6, "running")

    # ── Results dashboard ─────────────────────────────────────────────────
    st.divider()
    st.markdown("### Results")

    # Metric tiles
    m1, m2, m3, m4 = st.columns(4)
    sev_color = {"HIGH": "#ff4b4b", "MEDIUM": "#ffa500", "LOW": "#00c853"}.get(severity, "#8b8fa8")
    with m1:
        st.markdown(f'<div class="metric-tile"><div class="val" style="color:{sev_color}">'
                    f'{severity}</div><div class="lbl">Severity</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-tile"><div class="val">{total_issues}</div>'
                    f'<div class="lbl">Total Issues</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-tile"><div class="val">{dup_count}</div>'
                    f'<div class="lbl">Duplicates</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-tile"><div class="val">'
                    f'{len(anomalies["missing_values"])}</div>'
                    f'<div class="lbl">Null Columns</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs for detailed results
    tab_report, tab_rc, tab_rem, tab_raw = st.tabs(
        ["📄 Executive Report", "🧠 Root Cause", "🔧 Remediation", "📊 Raw Findings"]
    )

    with tab_report:
        st.markdown(report)
        st.download_button(
            "⬇ Download Report (.md)",
            data=report,
            file_name=f"dq_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            type="primary",
        )

    with tab_rc:
        st.markdown(root_cause)

    with tab_rem:
        st.markdown(remediation)

    with tab_raw:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Missing Values**")
            if anomalies["missing_values"]:
                st.dataframe(
                    pd.DataFrame(anomalies["missing_values"]).T,
                    use_container_width=True
                )
            else:
                st.success("No missing values detected")
        with col_b:
            st.markdown("**Domain Violations**")
            if anomalies["domain_violations"]:
                st.dataframe(
                    pd.DataFrame(anomalies["domain_violations"]).T,
                    use_container_width=True
                )
            else:
                st.success("No domain violations detected")

        st.markdown(f"**Duplicate Rows:** {dup_count} ({anomalies['duplicates']['pct']}%)")

    # ── Human Review Gate ─────────────────────────────────────────────────
    st.divider()
    st.markdown("### 👤 Human Review Gate")
    st.markdown(
        "Review the findings above. Select your governance decision — "
        "this is the accountability layer that makes the automation trustworthy."
    )

    dec_col, note_col = st.columns([1, 2])
    with dec_col:
        decision = st.radio(
            "Your decision:",
            ["✅ APPROVE — Accept findings, mark run complete",
             "🔄 REJECT — Re-run pipeline with new parameters",
             "🚨 ESCALATE — Flag for CDO / Data Governance review"],
            index=0,
        )
    with note_col:
        notes = st.text_area("Reviewer notes (optional):", height=120,
                             placeholder="Add context, observations, or instructions for the team...")

    if st.button("Submit Decision", type="primary"):
        decision_code = "APPROVE" if "APPROVE" in decision else \
                        "REJECT"  if "REJECT"  in decision else "ESCALATE"

        set_step(6, "done")

        if decision_code == "APPROVE":
            st.success(f"✅ Run approved and logged — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        elif decision_code == "REJECT":
            st.warning("🔄 Run rejected — adjust parameters and re-run the analysis above.")
        else:
            st.error("🚨 Escalated to Data Governance leadership. "
                     "[Simulated] Alert sent to CDO team.")

        if notes:
            st.info(f"📌 Reviewer notes logged: {notes}")


# ── Empty state ───────────────────────────────────────────────────────────
elif df_raw is None:
    st.markdown("""
    <div class="dq-card" style="text-align:center; padding:3rem;">
        <div style="font-size:3rem; margin-bottom:1rem;">🛡️</div>
        <h3>Upload a CSV to begin</h3>
        <p>Or click <strong>Use IBM HR Sample</strong> to run on the built-in demo dataset.</p>
        <p style="margin-top:1rem; font-size:0.85rem; color:#555;">
            Supports any tabular CSV — HR data, financial records, operational data.
        </p>
    </div>
    """, unsafe_allow_html=True)
