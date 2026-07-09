"""Export weather, risk, and price forecast data for the web dashboard."""
import json
import os
from datetime import datetime, timezone

from src.topology import NODES, EDGES, CROSS_SECTIONS
from src.weather import fetch_daily_forecast
from src.risk import assess_node_risk, assess_cross_section_risk


BASE_PRICE = 350.0
DEMAND_BONUS = {"medium": 10, "high": 20}
SUPPLY_BONUS = {"medium": 5, "high": 15}


def _date_str(dt):
    return dt.strftime("%m-%d")


def build_web_data(node_forecasts=None):
    os.makedirs("web", exist_ok=True)
    export_topology_json()
    dates = set()
    node_weather = {key: {} for key in NODES}
    all_risks = []

    for key, node in NODES.items():
        if node_forecasts is not None:
            df = node_forecasts.get(key)
            if df is None:
                continue
        else:
            df = fetch_daily_forecast(node["lat"], node["lon"], days=15)
        risks = assess_node_risk(key, node, df)
        all_risks.extend(risks)

        for _, row in df.iterrows():
            d = _date_str(row["date"])
            dates.add(d)
            node_weather[key][d] = {
                "tmax": round(row["tmax"], 1),
                "precip": round(row["precip"], 1),
            }

    dates = sorted(dates)

    cross_section_series = assess_cross_section_risk(
        CROSS_SECTIONS, NODES, node_weather, dates
    )

    price_series = []
    for d in dates:
        demand_risks = [r for r in all_risks if r["date"] == d and r["type"] == "需求侧高温"]
        supply_risks = [r for r in all_risks if r["date"] == d and r["type"] in ("供端降雨", "供端强降雨")]

        score = BASE_PRICE
        for r in demand_risks:
            weight = r.get("population_weight", 1.0)
            score += DEMAND_BONUS[r["level"]] * weight
        for r in supply_risks:
            score += SUPPLY_BONUS[r["level"]]

        affected_pop = sum(r.get("population", 0) for r in demand_risks) / 10000

        if demand_risks and supply_risks:
            risk_level = "high"
        elif demand_risks:
            risk_level = "medium"
        elif supply_risks:
            risk_level = "low"
        else:
            risk_level = "none"

        price_series.append({
            "date": d,
            "score": round(score, 1),
            "risk": risk_level,
            "demand_count": len(demand_risks),
            "supply_count": len(supply_risks),
            "affected_pop": round(affected_pop, 2),
        })

    nodes = {}
    for key, node in NODES.items():
        nodes[key] = {
            "name": node["name"],
            "type": node["type"],
            "lon": node["lon"],
            "lat": node["lat"],
            "population": node.get("population"),
            "population_weight": node.get("population_weight"),
            "weather": node_weather[key],
        }

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_price": BASE_PRICE,
        "dates": dates,
        "nodes": nodes,
        "price_series": price_series,
        "cross_sections": cross_section_series,
    }

    with open("web/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Exported web/data.json")


def export_topology_json():
    """Write web/topology.json from NODES and EDGES so the frontend stays in sync."""
    topology = {
        "nodes": {
            key: {
                "name": node["name"],
                "lat": node["lat"],
                "lon": node["lon"],
                "type": node["type"],
                "note": node.get("note", ""),
                "population": node.get("population"),
                "population_weight": node.get("population_weight"),
            }
            for key, node in NODES.items()
        },
        "edges": list(EDGES),
        "cross_sections": [
            {
                "id": cs["id"],
                "name": cs["name"],
                "type": cs["type"],
                "capacity_mw": cs["capacity_mw"],
                "edges": cs["edges"],
            }
            for cs in CROSS_SECTIONS
        ],
    }
    with open("web/topology.json", "w", encoding="utf-8") as f:
        json.dump(topology, f, ensure_ascii=False, indent=2)
    print("Exported web/topology.json")


if __name__ == "__main__":
    build_web_data()
