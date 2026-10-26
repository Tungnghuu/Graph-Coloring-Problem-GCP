from pysat.formula import CNF
from .base import Encoding
from ..utils.graph_validation import validate_encoding_input

class POPEncoding(Encoding):
    def __init__(self, symmetry_breaking: bool = False):
        self.symmetry_breaking = symmetry_breaking
        self.x_vars: dict[tuple[int, int], int] = {}
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

        x = self.x_vars
        cnf = CNF()

        if k == 0:
            if n > 0:
                cnf.append([])
            return cnf

        # ALO: each vertex must have ALO color
        for v in range(n):
            cnf.append([x[v, color] for color in range(k)])

        # AMO: each vertex must have AMO color
        for v in range(n):
            for color in range(k):
                for other_color in range(color + 1, k):
                    cnf.append([-x[v, color], -x[v, other_color]])

        # Adjacent vertices cannot share a color
        for u, v in edges:
            for color in range(k):
                cnf.append([-x[u, color], -x[v, color]])

        # Introduce a canonical order for first-use of colors.
        if self.symmetry_breaking:
            for v in range(min(n, k)):
                cnf.append(
                    [-x[v, color] for color in range(v + 1, k)]
                    + [x[v, v]]
                )
        return cnf