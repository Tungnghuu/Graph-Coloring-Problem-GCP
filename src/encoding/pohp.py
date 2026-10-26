from pysat.formula import CNF

from .base import Encoding
from ..utils.graph_validation import validate_encoding_input


class POHPEncoding(Encoding):
    def __init__(self, symmetry_breaking: bool = False):
        self.symmetry_breaking = symmetry_breaking
        self.x_vars: dict[tuple[int, int], int] = {}
        self.y_vars: dict[tuple[int, int], int] = {}
        self._n = None
        self._k = 0

    def encode(self, graph, k: int) -> CNF:
        n, edges = validate_encoding_input(graph, k)

        self._n, self._k = n, k
        self.x_vars = {
            (v, color): v * k + color + 1
            for v in range(n)
            for color in range(k)
        }
        self.y_vars = {
            (v, color): n * k + v * k + color + 1
            for v in range(n)
            for color in range(k)
        }
        x, y = self.x_vars, self.y_vars
        cnf = CNF()

        if k == 0:
            if n:
                cnf.append([])
            return cnf

        for v in range(n):
            cnf.append([-y[v, k - 1]])
            for color in range(k - 1):
                cnf.append([y[v, color], -y[v, color + 1]])

            cnf.append([x[v, 0], y[v, 0]])
            cnf.append([-x[v, 0], -y[v, 0]])

            for color in range(1, k):
                cnf.append([-x[v, color], y[v, color - 1]])
                cnf.append([-x[v, color], -y[v, color]])
                cnf.append([x[v, color], -y[v, color - 1], y[v, color]])

        for u, v in edges:
            for color in range(k):
                cnf.append([-x[u, color], -x[v, color]])

        if self.symmetry_breaking:
            for v in range(min(n, k)):
                cnf.append([-y[v, v]])

            for v in range(1, n):
                for color in range(1, min(k, v + 1)):
                    cnf.append(
                        [-x[v, color]]
                        + [x[u, color - 1] for u in range(color - 1, v)]
                    )

        return cnf