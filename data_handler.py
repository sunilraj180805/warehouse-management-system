import pandas as pd
import os
from datetime import datetime

PARTS_FILE   = "data/parts.csv"
USAGE_FILE   = "data/usage_log.csv"
RESTOCK_FILE = "data/restock_log.csv"


# ── helpers ───────────────────────────────────────────────────────────────────

def _ensure_dir():
    os.makedirs("data", exist_ok=True)


# ── parts ─────────────────────────────────────────────────────────────────────

def load_parts():
    _ensure_dir()
    if not os.path.exists(PARTS_FILE):
        df = pd.DataFrame(columns=[
            "part_id", "name", "count", "frequency",
            "threshold", "location", "movement_type",
            "previous_rank", "last_rearranged_date"
        ])
        df.to_csv(PARTS_FILE, index=False)
        return df

    df = pd.read_csv(PARTS_FILE, dtype={"part_id": str})
    return df


def save_parts(df):
    _ensure_dir()
    df.to_csv(PARTS_FILE, index=False)


# ── usage log ─────────────────────────────────────────────────────────────────

def load_usage_log():
    _ensure_dir()
    if not os.path.exists(USAGE_FILE):
        df = pd.DataFrame(columns=["part_id", "date", "quantity"])
        df.to_csv(USAGE_FILE, index=False)
        return df

    return pd.read_csv(USAGE_FILE, dtype={"part_id": str})


def append_usage_log(part_id, quantity):
    _ensure_dir()
    new_entry = pd.DataFrame([{
        "part_id":  str(part_id),
        "date":     datetime.now().strftime("%Y-%m-%d"),
        "quantity": quantity
    }])
    write_header = not os.path.exists(USAGE_FILE)
    new_entry.to_csv(USAGE_FILE, mode="a", header=write_header, index=False)


# ── restock log ───────────────────────────────────────────────────────────────

def load_restock_log():
    _ensure_dir()
    if not os.path.exists(RESTOCK_FILE):
        df = pd.DataFrame(columns=["part_id", "date", "quantity", "type"])
        df.to_csv(RESTOCK_FILE, index=False)
        return df

    df = pd.read_csv(RESTOCK_FILE, dtype={"part_id": str})
    # back-compat: if old file has no 'type' column add it
    if "type" not in df.columns:
        df["type"] = "Restock"
    return df


def append_restock_log(part_id, quantity, entry_type="Restock"):
    """
    entry_type: "New Part" when a part is first added, "Restock" for top-ups.
    """
    _ensure_dir()
    new_entry = pd.DataFrame([{
        "part_id":  str(part_id),
        "date":     datetime.now().strftime("%Y-%m-%d"),
        "quantity": quantity,
        "type":     entry_type
    }])
    write_header = not os.path.exists(RESTOCK_FILE)
    new_entry.to_csv(RESTOCK_FILE, mode="a", header=write_header, index=False)


# ── recency helper ────────────────────────────────────────────────────────────

def get_days_since_last_issue():
    """
    Returns { part_id (str) -> days since last issue (int) }
    Parts not in the log are NOT included — caller handles fallback.
    """
    usage_df = load_usage_log()

    if usage_df.empty:
        return {}

    usage_df["date"] = pd.to_datetime(usage_df["date"])
    last_issue = usage_df.groupby("part_id")["date"].max()
    today      = pd.Timestamp(datetime.now().date())
    days_map   = ((today - last_issue).dt.days).to_dict()

    return {str(k): int(v) for k, v in days_map.items()}