"""Risk rules and aggregation for Shandong grid trading support."""

from collections import defaultdict


def assess_node_risk(node_key, node, weather_df):
    """Return a list of risk events for a single node."""
    risks = []
    node_type = node["type"]
    name = node["name"]

    for _, row in weather_df.iterrows():
        date = row["date"].strftime("%m-%d")
        tmax = row["tmax"]
        precip = row["precip"]

        if node_type == "demand" and tmax > 33:
            risks.append(
                {
                    "date": date,
                    "node": name,
                    "node_key": node_key,
                    "type": "需求侧高温",
                    "level": "high" if tmax >= 36 else "medium",
                   "message": (
                       f"{name} {date} 最高温 {tmax:.1f}℃，"
                       f"空调负荷可能推升用电需求"
                   ),
                   "tmax": tmax,
                   "precip": precip,
                   "population": node.get("population"),
                   "population_weight": round(node.get("population_weight", 1.0), 3),
               }
           )

        if node_type == "supply":
            if precip >= 20:
                risks.append(
                    {
                        "date": date,
                        "node": name,
                        "node_key": node_key,
                        "type": "供端强降雨",
                        "level": "high",
                        "message": (
                            f"{name} {date} 降雨 {precip:.1f}mm，"
                            f"新能源出力或外送通道可能受限"
                        ),
                        "tmax": tmax,
                        "precip": precip,
                    }
                )
            elif precip >= 5:
                risks.append(
                    {
                        "date": date,
                        "node": name,
                        "node_key": node_key,
                        "type": "供端降雨",
                        "level": "medium",
                        "message": (
                            f"{name} {date} 降雨 {precip:.1f}mm，"
                            f"关注出力波动"
                        ),
                        "tmax": tmax,
                        "precip": precip,
                    }
                )

    return risks


def aggregate_price_risk(demand_risks, supply_risks):
    """Aggregate node-level risks into a simple price trend signal."""
    by_date = defaultdict(
        lambda: {
            "demand": [],
            "supply": [],
            "demand_count": 0,
            "supply_count": 0,
            "affected_pop": 0,
        }
    )

    for r in demand_risks:
        by_date[r["date"]]["demand"].append(r)
        by_date[r["date"]]["demand_count"] += 1
        if r.get("population"):
            by_date[r["date"]]["affected_pop"] += r["population"]

    for r in supply_risks:
        by_date[r["date"]]["supply"].append(r)
        by_date[r["date"]]["supply_count"] += 1

    results = []
    for date in sorted(by_date):
        d = by_date[date]["demand_count"]
        s = by_date[date]["supply_count"]
        affected_pop = by_date[date]["affected_pop"] / 10000
        if d > 0 and s > 0:
            risk = "high"
            message = (
                f"{date} 受端高温（{d}处，影响 {affected_pop:.0f} 万人）+ 供端降雨（{s}处），"
                f"电价上行风险高"
            )
        elif d > 0:
            risk = "medium"
            message = (
                f"{date} 受端高温（{d}处，影响 {affected_pop:.0f} 万人），"
                f"电价有上行压力"
            )
        elif s > 0:
            risk = "low"
            message = (
                f"{date} 供端降雨（{s}处），"
                f"关注供给端风险"
            )
        else:
            continue
        results.append(
            {
                "date": date,
                "risk": risk,
                "message": message,
                "affected_pop": round(affected_pop, 2),
            }
        )

    return results



def assess_cross_section_risk(cross_sections, nodes, node_weather, dates):
    """Return simplified daily utilization and risk for each cross-section.

    Demand cross-sections are stressed by high temperatures at load centers.
    Supply/renewable cross-sections are stressed by rainfall that reduces
    available inflow or renewable output.  This is a rule-of-thumb model
    for trading support, not a power-flow calculation.
    """
    base_util = {"demand": 0.60, "supply": 0.50, "renewable": 0.40}
    results = []
    for cs in cross_sections:
        base = base_util.get(cs["type"], 0.50)
        capacity = cs["capacity_mw"]
        touched = set()
        for a, b in cs["edges"]:
            touched.add(a)
            touched.add(b)
        for d in dates:
            stress = 0.0
            if cs["type"] == "demand":
                relevant = [k for k in touched if nodes[k]["type"] == "demand"]
                for k in relevant:
                    w = node_weather.get(k, {}).get(d)
                    if w and w["tmax"] > 33:
                        stress += (w["tmax"] - 33) / 3.0 * 0.06
            else:
                relevant = [k for k in touched if nodes[k]["type"] == "supply"]
                for k in relevant:
                    w = node_weather.get(k, {}).get(d)
                    if w and w["precip"] >= 5:
                        stress += min(w["precip"] / 20.0, 1.0) * 0.07

            utilization = min(0.95, base + stress)
            if utilization >= 0.85:
                level = "high"
            elif utilization >= 0.70:
                level = "medium"
            else:
                level = "low"
            load_mw = round(capacity * utilization, 0)
            results.append({
                "date": d,
                "id": cs["id"],
                "name": cs["name"],
                "type": cs["type"],
                "capacity_mw": capacity,
                "load_mw": load_mw,
                "utilization": round(utilization, 3),
                "risk": level,
                "message": (
                    f"{cs['name']} {d} 负载 {load_mw:.0f}/{capacity} MW "
                    f"（利用率 {utilization*100:.1f}%）"
                ),
            })
    return results
