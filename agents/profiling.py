"""
Agent 2 — Profiling
Computes completeness, uniqueness, validity, and distribution
statistics across the dataset — the foundation every downstream
agent reasons from.
"""

import pandas as pd


def profile_data(state: dict) -> dict:
    print("📊 [2/7] Profiling dataset ...")

    df: pd.DataFrame = state.get("raw_data")
    if df is None:
        state["errors"].append("Profiling skipped: no data available.")
        return state

    try:
        profile = {
            "row_count":      int(len(df)),
            "column_count":   int(len(df.columns)),
            "duplicate_rows": int(df.duplicated().sum()),
        }

        col_profiles = {}
        for col in df.columns:
            series = df[col]
            cp = {
                "dtype":        str(series.dtype),
                "null_count":   int(series.isna().sum()),
                "null_pct":     round(float(series.isna().mean() * 100), 2),
                "unique_count": int(series.nunique()),
            }
            if pd.api.types.is_numeric_dtype(series) and series.notna().any():
                desc = series.describe()
                cp.update({
                    "min":    round(float(desc["min"]), 4),
                    "max":    round(float(desc["max"]), 4),
                    "mean":   round(float(desc["mean"]), 4),
                    "std":    round(float(desc["std"]), 4) if pd.notna(desc["std"]) else 0.0,
                    "median": round(float(series.median()), 4),
                })
            col_profiles[col] = cp

        profile["columns"] = col_profiles
        profile["columns_with_nulls"] = [c for c, p in col_profiles.items() if p["null_count"] > 0]
        profile["high_null_cols"] = [c for c, p in col_profiles.items() if p["null_pct"] > 5]

        state["profile"] = profile
        print(f"   ✓ Profile complete: {profile['row_count']:,} rows | "
              f"{len(profile['columns_with_nulls'])} cols with nulls | "
              f"{profile['duplicate_rows']} duplicate rows")
        return state

    except Exception as e:
        state["errors"].append(f"Profiling error: {str(e)}")
        print(f"   ✗ Profiling failed: {e}")
        return state
