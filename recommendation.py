from scoring import calculate_scores
from data_handler import load_parts, save_parts
from datetime import datetime


def rank_parts(scores):
    """
    Assign ranks based on score.
    Higher score = better (closer) rank.
    """
    sorted_parts = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return {
        str(part_id): i + 1
        for i, (part_id, _) in enumerate(sorted_parts)
    }


def generate_recommendations():
    """
    Compare current ranks with newly calculated ranks
    and generate movement recommendations.
    """

    scores        = calculate_scores()
    current_ranks = rank_parts(scores)

    df = load_parts()

    recommendations = []

    for _, row in df.iterrows():

        part_id = str(row["part_id"])
        name    = row["name"]

        new_rank = current_ranks.get(part_id)

        if new_rank is None:
            continue

        old_rank = int(row.get("previous_rank", 0))

        # Skip if no change
        if old_rank != 0 and new_rank == old_rank:
            continue

        # Determine movement direction
        if old_rank == 0:
            direction = "NEW"
        else:
            change = old_rank - new_rank

            if change > 0:
                direction = "UP"
            else:
                direction = "DOWN"

        recommendations.append({
            "part_id":         part_id,
            "name":            name,
            "current_location": row["location"],
            "old_rank":        old_rank if old_rank != 0 else "-",
            "new_rank":        new_rank,
            "direction":       direction,
        })

    return recommendations, current_ranks


def apply_recommendations(current_ranks):

    df = load_parts()

    today = datetime.now().strftime("%Y-%m-%d")

    # ------------------------------------------------------------------
    # Sort warehouse locations
    # Nearest location = smallest sorted value
    # ------------------------------------------------------------------
    sorted_locations = sorted(
        df["location"]
        .astype(str)
        .str.upper()
        .str.strip()
        .tolist()
    )

    # rank -> location mapping
    rank_location_map = {
        rank: location
        for rank, location in enumerate(sorted_locations, start=1)
    }

    # ------------------------------------------------------------------
    # Apply updated ranks + mapped locations
    # ------------------------------------------------------------------
    for idx, row in df.iterrows():

        part_id = str(row["part_id"])

        if part_id in current_ranks:

            new_rank = current_ranks[part_id]

            df.at[idx, "previous_rank"] = new_rank

            # Assign location based on rank
            df.at[idx, "location"] = rank_location_map.get(
                new_rank,
                row["location"]
            )

            df.at[idx, "last_rearranged_date"] = today

    save_parts(df)

    return "Rearrangement applied successfully"