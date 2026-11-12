from math import isfinite
from numbers import Real
from time import perf_counter

def create_deadline(time_limit):
    if time_limit is None:
        return None

    is_boolean = isinstance(time_limit, bool)
    is_number = isinstance(time_limit, Real)
    if is_boolean or not is_number:
        raise TypeError("time_limit must be a number of seconds or None")

    is_finite = isfinite(time_limit)
    if not is_finite or time_limit <= 0:
        raise ValueError("time_limit must be a positive finite number")

    return perf_counter() + time_limit

def check_deadline(deadline):
    if deadline is None:
        return

    if perf_counter() >= deadline:
        raise TimeoutError("encoding time limit exceeded")

def effective_time_limit(time_limit, deadline):
    if deadline is None:
        return time_limit

    remaining = deadline - perf_counter()
    if remaining <= 0:
        raise TimeoutError("time limit exceeded")

    if time_limit is None:
        return remaining
    if time_limit < remaining:
        return time_limit
    return remaining

def validate_encoding_input(graph, k: int, *, deadline=None):
    check_deadline(deadline)

    # Check the number of colors
    k_is_integer = isinstance(k, int)
    k_is_boolean = isinstance(k, bool)
    if not k_is_integer or k_is_boolean:
        raise TypeError("k must be an integer")
    if k < 0:
        raise ValueError("k must be non-negative")

    has_vertex_count = hasattr(graph, "n")
    has_edges = hasattr(graph, "edges")
    if not has_vertex_count or not has_edges:
        raise TypeError("graph must provide n and edges")

    n = graph.n
    n_is_integer = isinstance(n, int)
    n_is_boolean = isinstance(n, bool)
    if not n_is_integer or n_is_boolean:
        raise TypeError("graph.n must be an integer")
    if n < 0:
        raise ValueError("graph.n must be non-negative")

    edges = set()
    for edge in graph.edges:
        check_deadline(deadline)
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

        if u < 0 or u >= n or v < 0 or v >= n:
            raise ValueError("edge endpoints must be in range(graph.n)")

        if u > v:
            u, v = v, u

        edges.add((u, v))

    return n, edges

def is_valid_coloring(graph):
    has_vertex_count = hasattr(graph, "n")
    has_edges = hasattr(graph, "edges")
    has_colors = hasattr(graph, "colors")
    if not has_vertex_count or not has_edges:
        return False

    if not has_colors:
        return False

    n = graph.n
    colors = graph.colors

    # Check that there is one color for every nodes
    n_is_integer = isinstance(n, int)
    n_is_boolean = isinstance(n, bool)
    if not n_is_integer or n_is_boolean or n < 0:
        return False

    try:
        colors = list(colors)
    except TypeError:
        return False

    if len(colors) != n:
        return False

    # Check that all assigned color numbers are non-negative
    for color in colors:
        color_is_integer = isinstance(color, int)
        color_is_boolean = isinstance(color, bool)
        if not color_is_integer or color_is_boolean:
            return False
        if color < 0:
            return False

    # Check that no edge connects vertices with the same color
    for edge in graph.edges:
        if len(edge) != 2:
            return False

        u, v = edge
        u_is_integer = isinstance(u, int)
        u_is_boolean = isinstance(u, bool)
        if not u_is_integer or u_is_boolean:
            return False

        v_is_integer = isinstance(v, int)
        v_is_boolean = isinstance(v, bool)
        if not v_is_integer or v_is_boolean:
            return False

        if u < 0 or u >= n or v < 0 or v >= n:
            return False
        if colors[u] == colors[v]:
            return False

    return True