import pandas as pd
from data_handler import (
    load_parts,
    save_parts,
    append_usage_log,
    append_restock_log,
)


def search_part(query):
    df     = load_parts()
    query  = str(query)
    result = df[
        (df["part_id"].str.upper() == query.upper()) |
        (df["name"].str.lower()    == query.lower())
    ]
    return None if result.empty else result.iloc[0]


def issue_part(part_id, quantity):
    df      = load_parts()
    part_id = str(part_id)

    if part_id not in df["part_id"].values:
        return "Part not found"
    if quantity <= 0:
        return "Invalid quantity"

    idx           = df[df["part_id"] == part_id].index[0]
    current_count = df.at[idx, "count"]

    if quantity > current_count:
        return "Not enough stock"

    df.at[idx, "count"]     = current_count - quantity
    df.at[idx, "frequency"] = int(df.at[idx, "frequency"]) + quantity

    save_parts(df)
    append_usage_log(part_id, quantity)
    return "Part issued successfully"


def restock_part(part_id, quantity):
    df      = load_parts()
    part_id = str(part_id)

    if part_id not in df["part_id"].values:
        return "Part not found"
    if quantity <= 0:
        return "Invalid quantity"

    idx              = df[df["part_id"] == part_id].index[0]
    df.at[idx, "count"] = int(df.at[idx, "count"]) + quantity

    save_parts(df)
    append_restock_log(part_id, quantity, entry_type="Restock")
    return "Part restocked successfully"


def add_new_part(part_id, name, count, threshold, movement_type, location):
    df      = load_parts()
    part_id = str(part_id).upper().strip()
    location = str(location).upper().strip()

    # ── uniqueness checks ─────────────────────────────────────────────────────
    if part_id in df["part_id"].values:
        return f"Part ID '{part_id}' already exists"

    if location:
        existing_locs = (
            df["location"]
            .astype(str)
            .str.upper()
            .str.strip()
            .values
        )
        if location in existing_locs:
            return f"Location '{location}' is already occupied"

    # ── next rank ─────────────────────────────────────────────────────────────
    next_rank = 1 if df.empty else int(df["previous_rank"].fillna(0).max()) + 1

    today = pd.Timestamp.today().strftime("%Y-%m-%d")

    new_row = pd.DataFrame([{
        "part_id":             part_id,
        "name":                name,
        "count":               count,
        "frequency":           0,
        "threshold":           threshold,
        "movement_type":       movement_type,
        "location":            location,
        "previous_rank":       int(next_rank),
        "last_rearranged_date": today,
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_parts(df)

    # Log the initial stock as a "New Part" entry in restock_log
    if count > 0:
        append_restock_log(part_id, count, entry_type="New Part")

    return f"Part '{part_id}' added successfully"