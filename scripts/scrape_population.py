"""Population data updater for Shandong demand cities.

The 9 demand nodes in this project are prefecture-level cities. County-level
data can be added later when the topology is refined.

Data source:
- Default: 第七次全国人口普查（2020）, stored in data/population.json.
- Optional: provide a custom data source via --url.

Official sources like the National Bureau of Statistics or Shandong Statistical
Yearbook are not easily machine-readable and often require anti-bot handling,
so the default is static census data. Replace this script with a production
pipeline when a stable API becomes available.
"""

import argparse
import json
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

DEFAULT_POPULATION = {
    "source": "第七次全国人口普查（2020）山东省各地市常住人口",
    "unit": "人",
    "census_year": 2020,
    "note": "当前项目仅覆盖 9 个受端负荷中心城市，人口作为需求权重使用。县域/区级数据可在后续扩展。",
    "cities": {
        "济南": 9202400,
        "青岛": 10071700,
        "烟台": 7102600,
        "潍坊": 9386700,
        "淄博": 4704100,
        "临沂": 11018400,
        "济宁": 8357900,
        "德州": 5611200,
        "聊城": 5952500,
    },
}


def load_existing(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def fetch_from_url(url):
    """Attempt to fetch population data from a custom URL.

    The caller is responsible for providing a JSON endpoint that returns the
    same shape as data/population.json.
    """
    if requests is None:
        raise RuntimeError("requests is required for fetching from URL")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    required = {"source", "unit", "cities"}
    if not required.issubset(data.keys()):
        raise ValueError(f"Response must contain keys: {required}")
    return data


def main():
    parser = argparse.ArgumentParser(description="Update population data for Shandong grid demand nodes.")
    parser.add_argument("--url", help="Optional JSON endpoint to fetch population data from.")
    parser.add_argument("--output", default="data/population.json", help="Output JSON path.")
    args = parser.parse_args()

    output_path = Path(args.output)

    if args.url:
        try:
            data = fetch_from_url(args.url)
            print(f"Fetched population data from {args.url}")
        except Exception as e:
            print(f"Fetch failed: {e}. Falling back to default census data.")
            data = DEFAULT_POPULATION
    else:
        existing = load_existing(output_path)
        if existing:
            print(f"Using existing {output_path}")
            data = existing
        else:
            print("Writing default census data.")
            data = DEFAULT_POPULATION

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
