"""Simplified Shandong grid topology based on public information.

The topology is intentionally schematic: it captures the major load centers
(demand nodes), external inflow points and renewable bases (supply nodes),
and representative transmission corridors. It is NOT the real State Grid
Shandong detailed topology.
"""

import json
from pathlib import Path


def _load_population():
    """Load city-level population from data/population.json.

    Falls back to an empty dict if the file is missing, so the rest of
    the pipeline still runs without population weighting.
    """
    pop_path = Path(__file__).parent.parent / "data" / "population.json"
    try:
        with open(pop_path, encoding="utf-8") as f:
            return json.load(f).get("cities", {})
    except FileNotFoundError:
        return {}


POPULATION = _load_population()

NODES = {
    # Demand / load centers (受端)
    "jinan": {
        "name": "济南",
        "lat": 36.67,
        "lon": 117.0,
        "type": "demand",
        "note": "省会负荷中心",
    },
    "qingdao": {
        "name": "青岛",
        "lat": 36.07,
        "lon": 120.38,
        "type": "demand",
        "note": "胶东负荷中心",
    },
    "yantai": {
        "name": "烟台",
        "lat": 37.46,
        "lon": 121.45,
        "type": "demand",
        "note": "胶东负荷中心",
    },
    "weifang": {
        "name": "潍坊",
        "lat": 36.71,
        "lon": 119.16,
        "type": "demand",
        "note": "鲁中负荷中心",
    },
    "zibo": {
        "name": "淄博",
        "lat": 36.81,
        "lon": 118.05,
        "type": "demand",
        "note": "鲁中负荷中心",
    },
    "linyi": {
        "name": "临沂",
        "lat": 35.05,
        "lon": 118.35,
        "type": "demand",
        "note": "鲁南负荷中心",
    },
    "jining": {
        "name": "济宁",
        "lat": 35.38,
        "lon": 116.38,
        "type": "demand",
        "note": "鲁南负荷中心",
    },
    "dezhou": {
        "name": "德州",
        "lat": 37.45,
        "lon": 116.35,
        "type": "demand",
        "note": "鲁西北负荷中心",
    },
    "liaocheng": {
        "name": "聊城",
        "lat": 36.45,
        "lon": 115.98,
        "type": "demand",
        "note": "鲁西北负荷中心",
    },
    # Supply / external inflow / generation bases (供端)
    "quancheng": {
        "name": "泉城站",
        "lat": 36.72,
        "lon": 117.05,
        "type": "supply",
        "note": "特高压交流外电入鲁",
    },
    "caozhou": {
        "name": "曹州站",
        "lat": 35.25,
        "lon": 115.45,
        "type": "supply",
        "note": "特高压交流外电入鲁",
    },
    "guanggu": {
        "name": "广固站",
        "lat": 36.75,
        "lon": 119.1,
        "type": "supply",
        "note": "鲁固直流东北外电",
    },
    "yinan": {
        "name": "沂南站",
        "lat": 35.55,
        "lon": 118.35,
        "type": "supply",
        "note": "昭沂直流西北外电",
    },
    "jiaodong": {
        "name": "胶东换",
        "lat": 37.2,
        "lon": 120.5,
        "type": "supply",
        "note": "银东直流西北外电",
    },
    "longdong": {
        "name": "陇东受端",
        "lat": 37.45,
        "lon": 116.35,
        "type": "supply",
        "note": "陇电入鲁直流",
    },
    "west_renewable": {
        "name": "西部风光",
        "lat": 36.85,
        "lon": 115.95,
        "type": "supply",
        "note": "省内西部风光基地",
    },
    "north_renewable": {
        "name": "北部风光",
        "lat": 37.85,
        "lon": 117.95,
        "type": "supply",
        "note": "省内北部风光基地",
    },
}

# Attach population and relative weight to demand nodes.
_demand_nodes = [n for n in NODES.values() if n["type"] == "demand" and n["name"] in POPULATION]
if _demand_nodes:
    _avg_pop = sum(POPULATION[n["name"]] for n in _demand_nodes) / len(_demand_nodes)
    for n in _demand_nodes:
        n["population"] = POPULATION[n["name"]]
        n["population_weight"] = n["population"] / _avg_pop

EDGES = [
    # Major transmission corridors from supply to demand
    ("quancheng", "jinan"),
    ("quancheng", "zibo"),
    ("caozhou", "jining"),
    ("caozhou", "jinan"),
    ("guanggu", "weifang"),
    ("guanggu", "qingdao"),
    ("yinan", "linyi"),
    ("yinan", "jining"),
    ("jiaodong", "yantai"),
    ("jiaodong", "qingdao"),
    ("longdong", "dezhou"),
    ("longdong", "jinan"),
    ("west_renewable", "liaocheng"),
    ("west_renewable", "dezhou"),
    ("north_renewable", "dezhou"),
    # Interconnectors among load centers
    ("jinan", "zibo"),
    ("jinan", "dezhou"),
    ("zibo", "weifang"),
    ("weifang", "qingdao"),
    ("weifang", "yantai"),
    ("qingdao", "yantai"),
    ("linyi", "jining"),
    ("linyi", "weifang"),
    ("dezhou", "liaocheng"),
]


def get_nodes_by_type(node_type):
    """Return a dict of nodes matching the given type."""
    return {k: v for k, v in NODES.items() if v["type"] == node_type}


# Simplified transmission cross-sections for trading risk analysis.
# Each cross-section groups a set of parallel corridors that share a
# similar function (e.g., load receiving, external inflow, renewable
# outflow). Capacities and membership are indicative only.
CROSS_SECTIONS = [
    {
        "id": "central_load",
        "name": "鲁中受端断面",
        "type": "demand",
        "capacity_mw": 30000,
        "edges": [
            ("quancheng", "jinan"),
            ("caozhou", "jinan"),
            ("longdong", "jinan"),
            ("jinan", "zibo"),
            ("jinan", "dezhou"),
            ("zibo", "weifang"),
        ],
    },
    {
        "id": "jiaodong_load",
        "name": "胶东受端断面",
        "type": "demand",
        "capacity_mw": 25000,
        "edges": [
            ("guanggu", "qingdao"),
            ("jiaodong", "qingdao"),
            ("jiaodong", "yantai"),
            ("weifang", "qingdao"),
            ("weifang", "yantai"),
            ("qingdao", "yantai"),
        ],
    },
    {
        "id": "lunan_load",
        "name": "鲁南受端断面",
        "type": "demand",
        "capacity_mw": 20000,
        "edges": [
            ("caozhou", "jining"),
            ("yinan", "linyi"),
            ("yinan", "jining"),
            ("linyi", "jining"),
            ("linyi", "weifang"),
        ],
    },
    {
        "id": "external_inflow",
        "name": "外电入鲁断面",
        "type": "supply",
        "capacity_mw": 35000,
        "edges": [
            ("quancheng", "jinan"),
            ("caozhou", "jining"),
            ("guanggu", "weifang"),
            ("yinan", "linyi"),
            ("jiaodong", "yantai"),
            ("longdong", "dezhou"),
        ],
    },
    {
        "id": "west_renewable",
        "name": "西部风光送出断面",
        "type": "renewable",
        "capacity_mw": 15000,
        "edges": [
            ("west_renewable", "liaocheng"),
            ("west_renewable", "dezhou"),
        ],
    },
    {
        "id": "north_renewable",
        "name": "北部风光送出断面",
        "type": "renewable",
        "capacity_mw": 12000,
        "edges": [
            ("north_renewable", "dezhou"),
        ],
    },
]
