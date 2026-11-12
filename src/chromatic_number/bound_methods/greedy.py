from .base import UpperBoundMethod

class Greedy(UpperBoundMethod):
    def find_upper_bound(self, graph) -> int:
        n, adjacency = _build_adjacency(graph)
        if n == 0:
            return 0

        # Visit vertices with the most neighbors first.
        vertices = _sort_vertices_by_degree(adjacency)
        colors = [-1] * n
        color_count = 0

        # Give each vertex the first color not used by its neighbors.
        for vertex in vertices:
            used_colors = set()
            for neighbor in adjacency[vertex]:
                neighbor_color = colors[neighbor]
                if neighbor_color != -1:
                    used_colors.add(neighbor_color)

            color = 0
            while color in used_colors:
                color += 1

            colors[vertex] = color
            if color + 1 > color_count:
                color_count = color + 1

        return color_count


def _build_adjacency(graph):
    has_vertex_count = hasattr(graph, "n")
    has_edges = hasattr(graph, "edges")
    if not has_vertex_count or not has_edges:
        raise TypeError("graph must provide n and edges")

    n_is_integer = isinstance(graph.n, int)
    n_is_boolean = isinstance(graph.n, bool)
    if not n_is_integer or n_is_boolean:
        raise TypeError("graph.n must be an integer")
    if graph.n < 0:
        raise ValueError("graph.n must be non-negative")

    # Start with an empty neighbor list for every vertex.
    adjacency = []
    for _ in range(graph.n):
        adjacency.append(set())

    # Add each valid edge to both vertices' neighbor lists.
    for edge in graph.edges:
        if len(edge) != 2:
            raise ValueError("each edge must contain two endpoints")

        u, v = edge
        u_is_integer = isinstance(u, int)
        u_is_boolean = isinstance(u, bool)
        if not u_is_integer or u_is_boolean:
            raise TypeError("edge endpoints must be integers")

        v_is_integer = isinstance(v, int)
        v_is_boolean = isinstance(v, bool)
        if not v_is_integer or v_is_boolean:
            raise TypeError("edge endpoints must be integers")

        if u < 0 or u >= graph.n or v < 0 or v >= graph.n:
            raise ValueError("edge endpoints must be in range(graph.n)")

        if u != v:
            adjacency[u].add(v)
            adjacency[v].add(u)

    return graph.n, adjacency


def _sort_vertices_by_degree(adjacency, vertices=None):
    # Sort by descending degree, then by vertex number.
    if vertices is None:
        vertices = range(len(adjacency))

    ordered_vertices = []
    for vertex in vertices:
        degree = len(adjacency[vertex])
        ordered_vertices.append((-degree, vertex))

    ordered_vertices.sort()

    vertices = []
    for _, vertex in ordered_vertices:
        vertices.append(vertex)
    return vertices