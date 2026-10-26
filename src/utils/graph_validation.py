def validate_encoding_input(graph, k: int):
    # Check color: k
    if not isinstance(k, int) or isinstance(k, bool):
        raise TypeError("k must be an integer")
    if k < 0:
        raise ValueError("k must be non-negative")

    # Check graph
    if not hasattr(graph, "n") or not hasattr(graph, "edges"):
        raise TypeError("graph must provide n and edges")

    n = graph.n
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("graph.n must be an integer")
    if n < 0:
        raise ValueError("graph.n must be non-negative")

    # Check edges
    edges = set()
    for edge in graph.edges:
        if len(edge) != 2:
            raise ValueError("each edge must contain two endpoints")

        u, v = edge
        if not isinstance(u, int) or isinstance(u, bool):
            raise TypeError("edge endpoints must be integers")
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError("edge endpoints must be integers")
        if u < 0 or u >= n or v < 0 or v >= n:
            raise ValueError("edge endpoints must be in range(graph.n)")

        if u > v:
            u, v = v, u

        edges.add((u, v))

    return n, edges

def is_valid_coloring(graph):
    # Check graph attributes
    if not hasattr(graph, "n") or not hasattr(graph, "edges"):
        return False

    if not hasattr(graph, "colors"):
        return False

    n = graph.n
    colors = graph.colors

    # Check number of colors assigned
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        return False

    try:
        colors = list(colors)
    except TypeError:
        return False

    if len(colors) != n:
        return False

    # Check color value
    for color in colors:
        if not isinstance(color, int) or isinstance(color, bool):
            return False
        if color < 0:
            return False

    # Check every edge
    for edge in graph.edges:
        if len(edge) != 2:
            return False

        u, v = edge
        if not isinstance(u, int) or isinstance(u, bool):
            return False
        if not isinstance(v, int) or isinstance(v, bool):
            return False
        if u < 0 or u >= n or v < 0 or v >= n:
            return False
        if colors[u] == colors[v]:
            return False
    return True