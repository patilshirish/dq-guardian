"""
get_dataset.py — One-time helper to fetch the IBM HR Attrition dataset
locally, used as a fallback if the HuggingFace load in agents/ingestion.py
fails (e.g., due to network restrictions or a renamed HF dataset repo).

USAGE:
    1. Go to: https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset
    2. Click "Download" (you may need a free Kaggle account)
    3. Unzip the download — you'll get a file named:
       WA_Fn-UseC_-HR-Employee-Attrition.csv
    4. Place that file inside this project's `data/` folder:
       dq-guardian/data/WA_Fn-UseC_-HR-Employee-Attrition.csv

That's it — agents/ingestion.py will automatically use this file if the
HuggingFace dataset load fails. No code changes needed.
"""

import os

EXPECTED_PATH = "data/WA_Fn-UseC_-HR-Employee-Attrition.csv"

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    if os.path.exists(EXPECTED_PATH):
        print(f"✓ Found dataset at {EXPECTED_PATH} — you're all set.")
    else:
        print(f"✗ Dataset not found at {EXPECTED_PATH}")
        print(__doc__)
