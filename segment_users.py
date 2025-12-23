import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

ALL_USERS_CSV = BASE_DIR / "all_users_analysis.csv"
SUBSET_USERS_CSV = BASE_DIR / "subset_all_users_analysis.csv"
README_PATH = BASE_DIR / "SEGMENT_README.md"

SEGMENT_COLUMN_NAME = "user_segment"


def parse_decimal(value: str) -> Decimal:
    """
    Safely parse a numeric string into Decimal.
    Falls back to 0 if parsing fails.
    """
    value = value.strip()
    if not value:
        return Decimal(0)
    try:
        # Remove any currency symbols or thousand separators if present
        cleaned = value.replace(",", "").replace("$", "")
        return Decimal(cleaned)
    except (InvalidOperation, AttributeError):
        return Decimal(0)


def classify_segment(cumulative_total_value_max: Decimal) -> str:
    """
    Classify user into Large / Medium / Small based on cumulative_total_value_max.
    Thresholds from user specification:
      - Large: >= 1_000_000
      - Medium: 10_000 <= x < 1_000_000
      - Small: everything else
    """
    one_million = Decimal("1000000")
    ten_thousand = Decimal("10000")

    if cumulative_total_value_max >= one_million:
        return "Large"
    if ten_thousand <= cumulative_total_value_max < one_million:
        return "Medium"
    return "Small"


def add_segments_to_csv(csv_path: Path):
    """
    Add a user_segment column to the given CSV (if not already present),
    and return counts for each segment.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])

        # Ensure the key column exists
        if "cumulative_total_value_max" not in fieldnames:
            raise KeyError(
                f"'cumulative_total_value_max' column not found in {csv_path.name}"
            )

        # Add the segment column if missing
        if SEGMENT_COLUMN_NAME not in fieldnames:
            fieldnames.append(SEGMENT_COLUMN_NAME)

        rows = []
        segment_counts = {"Large": 0, "Medium": 0, "Small": 0}

        for row in reader:
            value_str = row.get("cumulative_total_value_max", "")
            value_dec = parse_decimal(value_str)
            segment = classify_segment(value_dec)
            row[SEGMENT_COLUMN_NAME] = segment
            segment_counts[segment] += 1
            rows.append(row)

    # Write back to the same file
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return segment_counts


def write_readme(all_counts: dict, subset_counts: dict):
    """
    Create a README-style markdown file summarizing segment counts
    for both all_users_analysis.csv and subset_all_users_analysis.csv.
    """
    total_all = sum(all_counts.values())
    total_subset = sum(subset_counts.values())

    lines = []
    lines.append("# User Segmentation Summary")
    lines.append("")
    lines.append("This file summarizes user segments based on `cumulative_total_value_max`.")
    lines.append("")
    lines.append("## Segment Definitions")
    lines.append("")
    lines.append("- **Large User**: `cumulative_total_value_max` ≥ 1,000,000")
    lines.append("- **Medium User**: 10,000 ≤ `cumulative_total_value_max` < 1,000,000")
    lines.append("- **Small User**: All remaining users")
    lines.append("")
    lines.append("## Segment Counts")
    lines.append("")
    lines.append("### all_users_analysis.csv")
    lines.append("")
    lines.append(f"- **Total users**: {total_all}")
    lines.append(f"- **Large users**: {all_counts.get('Large', 0)}")
    lines.append(f"- **Medium users**: {all_counts.get('Medium', 0)}")
    lines.append(f"- **Small users**: {all_counts.get('Small', 0)}")
    lines.append("")
    lines.append("### subset_all_users_analysis.csv")
    lines.append("")
    lines.append(f"- **Total users**: {total_subset}")
    lines.append(f"- **Large users**: {subset_counts.get('Large', 0)}")
    lines.append(f"- **Medium users**: {subset_counts.get('Medium', 0)}")
    lines.append(f"- **Small users**: {subset_counts.get('Small', 0)}")
    lines.append("")

    README_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    print(f"Updating segments in: {ALL_USERS_CSV}")
    all_counts = add_segments_to_csv(ALL_USERS_CSV)
    print("all_users_analysis.csv segment counts:", all_counts)

    print(f"Updating segments in: {SUBSET_USERS_CSV}")
    subset_counts = add_segments_to_csv(SUBSET_USERS_CSV)
    print("subset_all_users_analysis.csv segment counts:", subset_counts)

    write_readme(all_counts, subset_counts)
    print(f"Segment README written to: {README_PATH}")


if __name__ == "__main__":
    main()


