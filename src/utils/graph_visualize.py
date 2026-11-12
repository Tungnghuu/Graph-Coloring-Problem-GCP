import colorsys
from pathlib import Path
import webbrowser

from pyvis.network import Network
from .graph_io import read_col

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

    # Generate more colors when the graph needs them.
    for i in range(n - len(palette)):
        hue = ((i * 137.508) % 360) / 360
        r, g, b = colorsys.hls_to_rgb(hue, 0.5, 0.95)
        red = int(r * 255)
        green = int(g * 255)
        blue = int(b * 255)
        palette.append(
            "#{:02X}{:02X}{:02X}".format(
                red, green, blue
            )
        )
    return palette

def draw_graph(graph, output_path="graph.html", open_browser=True):
    # Set up the graph display.
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
        color_number = graph.colors[v]
        if color_number is None:
            color = "lightgray"
        else:
            color = palette[color_number % len(palette)]

        net.add_node(
            v,
            label = str(v),
            color = color,
            borderWidth = 1,
            borderWidthSelected = 4,
            size = 18,
            font = {"size": 16, "color": "black"},
            title = f"Color index: {color_number}"
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

    # Save the HTML page and optionally open it in a browser.
    output_path = Path(output_path).resolve()
    html = net.generate_html(notebook=False)
    output_path.write_text(html, encoding="utf-8")
    if open_browser:
        webbrowser.open(output_path.as_uri())
    return output_path

if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parents[2]
    graph = read_col(str(project_dir / "data" / "250" / "anna.col"))
    graph.colors = [None] * graph.n

    for v in graph.get_vertices():
        neighbor_colors = set()
        for u, w in graph.edges:
            if w == v:
                neighbor_colors.add(graph.colors[u])
            if u == v:
                neighbor_colors.add(graph.colors[w])

        color = 0
        while color in neighbor_colors:
            color += 1

        graph.colors[v] = color

    draw_graph(graph)