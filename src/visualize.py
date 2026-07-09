"""Visualize the simplified grid topology."""

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx


def _configure_chinese_font():
    """Try to use a Chinese font; fallback to default if not available."""
    preferred = [
        "Arial Unicode MS",
        "PingFang SC",
        "Heiti TC",
        "SimHei",
        "Microsoft YaHei",
    ]
    available = set(f.name for f in matplotlib.font_manager.fontManager.ttflist)
    for font in preferred:
        if font in available:
            plt.rcParams["font.sans-serif"] = [font]
            break
    plt.rcParams["axes.unicode_minus"] = False


def draw_topology(nodes, edges, output_path="output/topology.png"):
    """Draw a geographic map of the simplified grid topology."""
    _configure_chinese_font()

    G = nx.Graph()
    for key, attrs in nodes.items():
        G.add_node(key, **attrs)
    G.add_edges_from(edges)

    # Geographic layout
    pos = {key: (attrs["lon"], attrs["lat"]) for key, attrs in nodes.items()}

    color_map = {
        "demand": "#e74c3c",
        "supply": "#2ecc71",
    }

    node_colors = [color_map[attrs["type"]] for attrs in nodes.values()]

    fig, ax = plt.subplots(figsize=(14, 12))
    nx.draw_networkx_edges(
        G, pos, edge_color="#95a5a6", alpha=0.6, width=1.5, ax=ax
    )
    nx.draw_networkx_nodes(
        G, pos, node_color=node_colors, node_size=400, alpha=0.9, ax=ax
    )
    nx.draw_networkx_labels(
        G, pos, labels={k: v["name"] for k, v in nodes.items()},
        font_size=9,
        font_family="sans-serif",
        ax=ax,
    )

    ax.set_title("山东电网简化拓扑（示意）")
    ax.set_xlabel("经度")
    ax.set_ylabel("纬度")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="datalim")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Topology saved to {output_path}")
