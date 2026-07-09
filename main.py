"""Entry point for Shandong grid risk analysis."""

import os

from src.topology import EDGES, NODES, CROSS_SECTIONS
from src.risk import aggregate_price_risk, assess_node_risk, assess_cross_section_risk
from src.visualize import draw_topology
from src.weather import fetch_daily_forecast

from src.export_web_data import build_web_data


def main():
    os.makedirs("output", exist_ok=True)
    draw_topology(NODES, EDGES, "output/topology.png")

    print("正在获取未来 15 天天气数据...")
    demand_risks = []
    supply_risks = []
    node_forecasts = {}

    for key, node in NODES.items():
        try:
            df = fetch_daily_forecast(node["lat"], node["lon"], days=15)
            node_forecasts[key] = df
            risks = assess_node_risk(key, node, df)
            if node["type"] == "demand":
                demand_risks.extend(risks)
            else:
                supply_risks.extend(risks)
        except Exception as e:
            print(f"  {node['name']} 天气数据获取失败：{e}")

    print("\n=== 节点级风险预警 ===")
    for r in demand_risks + supply_risks:
        print(f"[{r['level'].upper()}] {r['message']}")

    print("\n=== 综合电价风险 ===")
    for r in aggregate_price_risk(demand_risks, supply_risks):
        print(f"[{r['risk'].upper()}] {r['message']}")

    print("\n=== 输电断面风险 ===")
    node_weather = {}
    dates = set()
    for key, df in node_forecasts.items():
        node_weather[key] = {}
        for _, row in df.iterrows():
            d = row["date"].strftime("%m-%d")
            dates.add(d)
            node_weather[key][d] = {
                "tmax": round(row["tmax"], 1),
                "precip": round(row["precip"], 1),
            }
    cross_section_series = assess_cross_section_risk(
        CROSS_SECTIONS, NODES, node_weather, sorted(dates)
    )
    significant_cs = [cs for cs in cross_section_series if cs["risk"] in ("high", "medium")]
    for cs in significant_cs:
        print(f"[{cs['risk'].upper()}] {cs['message']}")

    if not demand_risks and not supply_risks and not significant_cs:
        print("未来 15 天未触发显著风险规则。")

    build_web_data(node_forecasts)


if __name__ == "__main__":
    main()
