from pysat.formula import CNF

from .base import Encoding


class SATEncoding(Encoding):
    """Direct one-hot encoding of graph coloring."""

    def __init__(self):
        self.x_vars = {}
        self._n = None
        self._k = None

    def encode(self, graph, k: int) -> CNF:
        n, edges = self._validate(graph, k)
        self._n, self._k = n, k
        self.x_vars = {
            (vertex, color): vertex * k + color + 1
            for vertex in range(n)
            for color in range(k)
        }
        cnf = CNF()

        if k == 0:
            if n:
                cnf.append([])
            return cnf

        for vertex in range(n):
            variables = [self.x_vars[vertex, color] for color in range(k)]
            cnf.append(variables)
            for index, variable in enumerate(variables):
                for other in variables[index + 1:]:
                    cnf.append([-variable, -other])

        for u, v in edges:
            for color in range(k):
                cnf.append([-self.x_vars[u, color], -self.x_vars[v, color]])

        return cnf

    @staticmethod
    def _validate(graph, k: int):
        if isinstance(k, bool) or not isinstance(k, int):
            raise TypeError("k must be an integer")
        if k < 0:
            raise ValueError("k must be non-negative")
        if not hasattr(graph, "n") or not hasattr(graph, "edges"):
            raise TypeError("graph must provide n and edges")
        n = graph.n
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError("graph.n must be an integer")
        if n < 0:
            raise ValueError("graph.n must be non-negative")

        edges = []
        for edge in graph.edges:
            if len(edge) != 2:
                raise ValueError("each edge must contain two endpoints")
            u, v = edge
            if any(isinstance(endpoint, bool) or not isinstance(endpoint, int)
                   for endpoint in (u, v)):
                raise TypeError("edge endpoints must be integers")
            if not 0 <= u < n or not 0 <= v < n:
                raise ValueError("edge endpoints must be in range(graph.n)")
            if u == v:
                edges.append((u, v))
            else:
                edges.append((min(u, v), max(u, v)))
        return n, set(edges)

    def decode_model(self, model: list[int]) -> list[int]:
        if self._n is None or self._k is None:
            raise RuntimeError("encode() must be called before decode_model()")
        if model is None:
            raise ValueError("cannot decode an absent or unsatisfiable model")
        positive = set(model)
        colors = []
        for vertex in range(self._n):
            assigned = [
                color for color in range(self._k)
                if self.x_vars[vertex, color] in positive
            ]
            if len(assigned) != 1:
                raise ValueError(f"model must assign exactly one color to vertex {vertex}")
            colors.append(assigned[0])
        return colors
    