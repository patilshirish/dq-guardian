"""
Agent 3 — Anomaly Detection
Flags violations across missing data, statistical outliers, and
domain-specific rules for HR data, then scores overall severity.
"""

import pandas as pd
import numpy as np


# Domain rules specific to the IBM HR Attrition schema. Each rule
# returns True for rows that VIOLATE the rule.
DOMAIN_RULES = {
    "Age":                  ("Age must be between 16 and 100",        lambda x: (x < 16) | (x > 100)),
    "DistanceFromHome":     ("DistanceFromHome cannot be negative",    lambda x: x < 0),
    "TotalWorkingYears":    ("TotalWorkingYears cannot be negative",   lambda x: x < 0),
    "Education":            ("Education must be coded 1-5",            lambda x: (x < 1) | (x > 5)),
    "EnvironmentSatisfaction": ("Satisfaction scores must be coded 1-4", lambda x: (x < 1) | (x > 4)),
    "JobSatisfaction":      ("Satisfaction scores must be coded 1-4",   lambda x: (x < 1) | (x > 4)),
    "WorkLifeBalance":      ("WorkLifeBalance must be coded 1-4",       lambda x: (x < 1) | (x > 4)),
}


def detect_anomalies(state: dict) -> dict:
    print("🔍 [3/7] Detecting anomalies ...")

    df: pd.DataFrame = state.get("raw_data")
    profile: dict = state.get("profile", {})

    if df is None:
        state["errors"].append("Anomaly detection skipped: no data.")
        return state

    anomalies = {
        "missing_values":    {},
        "iqr_outliers":      {},
        "domain_violations": {},
        "duplicates":        {},
        "summary":           {},
    }

    col_profiles = profile.get("columns", {})

    # ── 1. Missing values ─────────────────────────────────────────────
    for col, cp in col_profiles.items():
        if cp["null_count"] > 0:
            anomalies["missing_values"][col] = {
                "count": cp["null_count"],
                "pct":   cp["null_pct"],
            }

    # ── 2. IQR outliers (numeric columns only) ────────────────────────
    for col in df.select_dtypes(include=[np.number]).columns:
        try:
            series = df[col].dropna().astype(float)
            if series.empty:
                continue
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mask = (series < lo) | (series > hi)
            cnt = int(mask.sum())
            if cnt > 0:
                anomalies["iqr_outliers"][col] = {
                    "count": cnt,
                    "pct":   round(cnt / len(df) * 100, 2),
                    "lower_fence": round(float(lo), 2),
                    "upper_fence": round(float(hi), 2),
                }
        except Exception:
            continue

    # ── 3. Domain rule violations ──────────────────────────────────────
    for col, (rule_desc, rule_fn) in DOMAIN_RULES.items():
        if col in df.columns:
            try:
                series = df[col].dropna().astype(float)
                mask = rule_fn(series)
                cnt = int(mask.sum())
                if cnt > 0:
                    anomalies["domain_violations"][col] = {
                        "count": cnt,
                        "rule":  rule_desc,
                    }
            except Exception:
                continue

    # ── 4. Duplicates ───────────────────────────────────────────────────
    dup_count = int(df.duplicated().sum())
    anomalies["duplicates"] = {
        "count": dup_count,
        "pct":   round(dup_count / len(df) * 100, 2) if len(df) else 0.0,
    }

    # ── Summary + severity scoring ──────────────────────────────────────
    total_issues = (
        sum(v["count"] for v in anomalies["missing_values"].values())
        + sum(v["count"] for v in anomalies["domain_violations"].values())
        + dup_count
    )
    anomalies["summary"] = {
        "total_issues_detected":          total_issues,
        "columns_with_missing":           len(anomalies["missing_values"]),
        "columns_with_iqr_outliers":       len(anomalies["iqr_outliers"]),
        "columns_with_domain_violations":  len(anomalies["domain_violations"]),
        "duplicate_rows":                 dup_count,
        "severity": "HIGH" if total_issues > 60 else "MEDIUM" if total_issues > 20 else "LOW",
    }

    state["anomalies"] = anomalies
    print(f"   ✓ Detected {total_issues:,} issues | "
          f"Severity: {anomalies['summary']['severity']}")
    return state
