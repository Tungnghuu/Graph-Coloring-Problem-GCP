from .base import UpperBoundMethod

class Greedy(UpperBoundMethod):
    def find_upper_bound(self, graph) -> int:
        n, adjacency = _build_adjacency(graph)
        if n == 0:
            return 0

        vertices = sorted(
            range(n),
            key=lambda vertex: (-len(adjacency[vertex]), vertex),
        )
        colors = [-1] * n
        color_count = 0

        for vertex in vertices:
            used_colors = {
                colors[neighbor]
                for neighbor in adjacency[vertex]
                if colors[neighbor] != -1
            }
            color = 0
            while color in used_colors:
                color += 1
            colors[vertex] = color
            color_count = max(color_count, color + 1)

        return color_count


def _build_adjacency(graph):
    if not hasattr(graph, "n") or not hasattr(graph, "edges"):
        raise TypeError("graph must provide n and edges")
    if not isinstance(graph.n, int) or isinstance(graph.n, bool):
        raise TypeError("graph.n must be an integer")
    if graph.n < 0:
        raise ValueError("graph.n must be non-negative")

    adjacency = [set() for _ in range(graph.n)]
    for edge in graph.edges:
        if len(edge) != 2:
            raise ValueError("each edge must contain two endpoints")
        u, v = edge
        if not isinstance(u, int) or isinstance(u, bool):
            raise TypeError("edge endpoints must be integers")
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError("edge endpoints must be integers")
        if u < 0 or u >= graph.n or v < 0 or v >= graph.n:
            raise ValueError("edge endpoints must be in range(graph.n)")
        if u != v:
            adjacency[u].add(v)
            adjacency[v].add(u)
    return graph.n, adjacency