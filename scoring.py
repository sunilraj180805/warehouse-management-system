from data_handler import load_parts, get_days_since_last_issue
import pandas as pd

# ── Movement type weights ─────────────────────────────────────────────────────
WEIGHTS = {
    "Fast": 1.5,
    "Slow": 1.0,
    "Rare": 0.5,
    None:   1.0,
    "":     1.0,
}

# ── Recency decay per movement type ──────────────────────────────────────────
DECAY = {
    "Fast": 0.5,
    "Slow": 0.3,
    "Rare": 0.1,
    None:   0.0,
    "":     0.0,
}


def calculate_scores():
    parts_df       = load_parts()
    days_since_map = get_days_since_last_issue()

    scores = {}

    for _, row in parts_df.iterrows():
        part_id   = str(row["part_id"])
        frequency = int(row.get("frequency", 0))

        raw_type = row.get("movement_type", None)
        if pd.isna(raw_type) or str(raw_type).strip() == "":
            movement_type = None
        else:
            movement_type = str(raw_type).strip()

        weight     = WEIGHTS.get(movement_type, 1.0)
        base_score = frequency * weight

        decay = DECAY.get(movement_type, 0.0)

        if part_id in days_since_map:
            penalty = days_since_map[part_id] * decay
        else:
            if movement_type == "Fast":
                penalty = 30 * decay
            elif movement_type == "Slow":
                penalty = 20 * decay
            elif movement_type == "Rare":
                penalty = 10 * decay
            else:
                penalty = 0.0

        scores[part_id] = max(0, base_score - penalty)

    return scores