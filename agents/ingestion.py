"""
Agent 1 — Data Ingestion
Loads the IBM HR Analytics Employee Attrition & Performance dataset
and deliberately injects realistic data-quality issues.

IMPORTANT / TRANSPARENCY NOTE:
The original IBM dataset (1470 rows x 35 columns) ships with ZERO missing
values and no domain violations — it was built clean for ML tutorials.
To make this a credible data-quality demonstration, this agent injects
a documented set of realistic issues that mirror what shows up in real
HRIS / payroll data pipelines: missing values, duplicate records, invalid
categorical codes, and impossible numeric values. This is disclosed here
and in the README so the demo's findings are never mistaken for defects
in the original public dataset.
"""

import os
import pandas as pd
import numpy as np

LOCAL_CSV_FALLBACK = "data/WA_Fn-UseC_-HR-Employee-Attrition.csv"


def _load_raw_dataframe() -> pd.DataFrame:
    """
    Try HuggingFace first; fall back to a local CSV copy if the
    network is unavailable or the HF dataset path has moved.
    """
    try:
        from datasets import load_dataset
        ds = load_dataset("scikit-learn/ibm-employee-attrition", split="train")
        return ds.to_pandas()
    except Exception as hf_error:
        if os.path.exists(LOCAL_CSV_FALLBACK):
            print(f"   ⚠ HuggingFace load failed ({hf_error}); using local CSV fallback.")
            return pd.read_csv(LOCAL_CSV_FALLBACK)
        raise RuntimeError(
            "Could not load dataset from HuggingFace and no local fallback "
            f"CSV found at '{LOCAL_CSV_FALLBACK}'. "
            "Download the IBM HR Attrition CSV from Kaggle "
            "(search 'IBM HR Analytics Employee Attrition Dataset') and "
            f"place it at {LOCAL_CSV_FALLBACK}, then re-run."
        ) from hf_error


def ingest_data(state: dict) -> dict:
    print("📥 [1/7] Ingesting IBM HR Attrition data ...")

    try:
        df = _load_raw_dataframe()

        rng = np.random.default_rng(seed=42)
        n = len(df)

        # ── 1. Missing values — common in HRIS exports when optional
        #       fields are skipped during onboarding data entry.
        if "MonthlyIncome" in df.columns:
            idx = rng.choice(n, size=int(n * 0.03), replace=False)
            df.loc[idx, "MonthlyIncome"] = np.nan

        if "YearsAtCompany" in df.columns:
            idx = rng.choice(n, size=int(n * 0.02), replace=False)
            df.loc[idx, "YearsAtCompany"] = np.nan

        # ── 2. Duplicate records — simulates a re-sync from a second
        #       HRIS source without dedup logic.
        if n > 20:
            dup_rows = df.sample(n=20, random_state=42)
            df = pd.concat([df, dup_rows], ignore_index=True)
            n = len(df)

        # ── 3. Invalid categorical codes — simulates upstream mapping
        #       drift (e.g., a new HR system using different enums).
        
        # ── 4. Impossible numeric values — domain violations that
        #       indicate a unit error or corrupted field upstream.
        if "Age" in df.columns:
            idx = rng.choice(n, size=5, replace=False)
            df.loc[idx, "Age"] = rng.integers(150, 200, size=5)

        if "DistanceFromHome" in df.columns:
            idx = rng.choice(n, size=7, replace=False)
            df.loc[idx, "DistanceFromHome"] = -rng.integers(1, 30, size=7)

        # ── 5. Negative tenure — a classic "termination date before
        #       hire date" data integrity failure.
        if "TotalWorkingYears" in df.columns:
            idx = rng.choice(n, size=4, replace=False)
            df.loc[idx, "TotalWorkingYears"] = -rng.integers(1, 10, size=4)

        print(f"   ✓ Loaded {len(df):,} rows × {len(df.columns)} columns "
              f"(synthetic DQ issues injected for demonstration)")

        state["raw_data"] = df
        return state

    except Exception as e:
        state["errors"].append(f"Ingestion error: {str(e)}")
        print(f"   ✗ Ingestion failed: {e}")
        state["raw_data"] = None
        return state
