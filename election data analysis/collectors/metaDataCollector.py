import requests
import csv

GAMMA_BASE = "https://gamma-api.polymarket.com"

def fetch_event(event_slug: str) -> dict:
    url = f"{GAMMA_BASE}/events/slug/{event_slug}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def flatten_event_markets(event: dict) -> list[dict]:
    """
    Given event object with `markets` array, return a list of flattened rows:
    each row corresponds to one market, with event + market fields.
    """
    rows = []
    event_fields = {
        "event_id": event.get("id"),
        "event_slug": event.get("slug"),
        "event_title": event.get("title"),
        "event_startDate": event.get("startDate"),
        "event_endDate": event.get("endDate"),
        # add more as needed
    }
    markets = event.get("markets", [])
    for m in markets:
        row = {}
        row.update(event_fields)
        # add market-level fields
        row["market_id"] = m.get("id")
        row["market_slug"] = m.get("slug")
        row["market_question"] = m.get("question")
        row["market_startDate"] = m.get("startDate")
        row["market_endDate"] = m.get("endDate")
        row["market_outcomes"] = m.get("outcomes")
        row["volume"] = m.get("volume")
        # add more market fields as needed
        rows.append(row)
    return rows

def write_rows_to_csv(rows: list[dict], filename: str):
    if not rows:
        print("No rows to write")
        return
    fieldnames = sorted(rows[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def main():
    slug = "romania-presidential-election-winner"
    event = fetch_event(slug)
    rows = flatten_event_markets(event)
    output_file = f"meta_{slug}_markets.csv"
    write_rows_to_csv(rows, output_file)
    print(f"Wrote {len(rows)} rows to {output_file}")

if __name__ == "__main__":
    main()
