from pysat.formula import CNF

from .base import Encoding


class POHPEncoding(Encoding):

    def __init__(self, symmetry_breaking: bool = False):
        self.symmetry_breaking = symmetry_breaking
        self.x_vars: dict[tuple[int, int], int] = {}
        self.y_vars: dict[tuple[int, int], int] = {}
        self._n = None
        self._k = 0

    def encode(self, graph, k: int) -> CNF:
    
        if isinstance(k, bool) or not isinstance(k, int):
            raise TypeError("k must be an integer")
        if k < 0:
            raise ValueError("k must be non-negative")

        n = graph.n
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError("graph.n must be an integer")
        if n < 0:
            raise ValueError("graph.n must be non-negative")

        edges = list(graph.edges)
        for u, v in edges:
            for endpoint in (u, v):
                if isinstance(endpoint, bool) or not isinstance(endpoint, int):
                    raise TypeError("edge endpoints must be integers")
                if not 0 <= endpoint < n:
                    raise ValueError("edge endpoints must be in range(graph.n)")

        self._n, self._k = n, k
        self.x_vars = {
            (v, i): v * k + i
            for v in range(n)
            for i in range(1, k + 1)
        }
        self.y_vars = {
            (v, i): n * k + v * k + i
            for v in range(n)
            for i in range(1, k + 1)
        }
        x, y = self.x_vars, self.y_vars
        cnf = CNF()

        if k == 0:
            if n:
                cnf.append([])
            return cnf

        for v in range(n):

            cnf.append([-y[v, k]])
            for i in range(1, k):
                cnf.append([y[v, i], -y[v, i + 1]])

        
            cnf.append([x[v, 1], y[v, 1]])
            cnf.append([-x[v, 1], -y[v, 1]])

            for i in range(2, k + 1):
                cnf.append([-x[v, i], y[v, i - 1]])
                cnf.append([-x[v, i], -y[v, i]])
                cnf.append([x[v, i], -y[v, i - 1], y[v, i]])


        for u, v in edges:
            for i in range(1, k + 1):
                cnf.append([-x[u, i], -x[v, i]])

        if self.symmetry_breaking:
    
            for v in range(min(n, k)):
                cnf.append([-y[v, v + 1]])

            
            for v in range(1, n):
                for i in range(2, min(k, v + 1) + 1):
                    cnf.append(
                        [-x[v, i]] + [x[u, i - 1] for u in range(i - 2, v)]
                    )

        return cnf

    def decode_model(self, model: list[int]) -> list[int]:
        
        if self._n is None:
            raise RuntimeError("encode() must be called before decode_model()")
        if model is None:
            raise ValueError("cannot decode an absent or unsatisfiable model")

        positive = {literal for literal in model if literal > 0}
        colors = []
        for v in range(self._n):
            assigned = [
                i - 1
                for i in range(1, self._k + 1)
                if self.x_vars[v, i] in positive
            ]
            if len(assigned) != 1:
                raise ValueError(f"model must assign exactly one color to vertex {v}")
            colors.append(assigned[0])
        return colors
