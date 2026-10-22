
from pyvis.network import Network
from graph_io import read_col
import colorsys
import os
import webbrowser

def create_palette(n=100):
    palette = [
        "#E6194B", "#3CB44B", "#4363D8", "#FFE119",
        "#F58231", "#911EB4", "#42D4F4", "#F032E6",
        "#BFEF45", "#FABED4", "#469990", "#DCBEFF",
        "#9A6324", "#800000", "#000075", "#A9A9A9",
        "#000000", "#FF6347", "#008080", "#6A5ACD",
    ]

    if n <= len(palette):
        return palette[:n]

    # generate more colors if needed
    for i in range(n - len(palette)):
        hue = ((i * 137.508) % 360) / 360
        r, g, b = colorsys.hls_to_rgb(hue, 0.5, 0.95)
        palette.append(
            "#{:02X}{:02X}{:02X}".format(
                int(r * 255), int(g * 255), int(b * 255)
            )
        )
    return palette

def draw_graph(graph):
    net = Network(
        height="750px",
        width="100%",
        bgcolor="white",
        notebook=False,
        cdn_resources="in_line"
    )

    net.barnes_hut(
        gravity = -8000,
        central_gravity = 0.05,
        spring_length = 200,
        spring_strength = 0.01,
        damping = 0.85
    )

    palette = create_palette(100)

    for v in graph.get_vertices():
        c = graph.colors[v]
        color = "lightgray" if c is None else palette[c % len(palette)]

        net.add_node(
            v,
            label = str(v),
            color = color,
            borderWidth = 1,
            borderWidthSelected = 4,
            size = 18,
            font = {"size": 16, "color": "black"},
            title = f"Color index: {c}"
        )

    for u, v in graph.edges:
        net.add_edge(
            u, v,
            color = {
                "color": "#999999",
                "highlight": "#222222",
                "hover": "#222222",
                "inherit": False
            },
            width = 1
        )

    output_path = os.path.abspath("graph.html")
    html = net.generate_html(notebook=False)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open("file:///" + output_path.replace("\\", "/"))

if __name__ == "__main__":
    graph = read_col("data/instances/anna.col")
    graph.colors = [None] * 139

    for v in graph.get_vertices():
        neighbor_colors = {
            graph.colors[u]
            for u, w in graph.edges if w == v
        } | {
            graph.colors[w]
            for u, w in graph.edges if u == v
        }

        color = 0
        while color in neighbor_colors:
            color += 1

        graph.colors[v] = color

    draw_graph(graph)
