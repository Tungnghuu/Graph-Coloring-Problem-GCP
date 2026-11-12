from pysat.formula import CNF
from .base import CNFEncoding
from ..utils.graph_validation import validate_encoding_input

class POHPEncoding(CNFEncoding):
    def __init__(self, symmetry_breaking: bool = True):
        self.symmetry_breaking = symmetry_breaking
        self.x_vars: dict[tuple[int, int], int] = {}
        self.y_vars: dict[tuple[int, int], int] = {}
        self._n = None
        self._k = 0

    def encode(self, graph, k: int, *, time_limit=None) -> CNF:
        deadline = self._encoding_deadline(time_limit)
        n, edges = validate_encoding_input(graph, k, deadline=deadline)

        self._n, self._k = n, k
        self.x_vars = {}
        self.y_vars = {}
        for v in range(n):
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                self.x_vars[v, color] = v * k + color + 1
                self.y_vars[v, color] = n * k + v * k + color + 1
        x, y = self.x_vars, self.y_vars
        cnf = CNF()

        if k == 0:
            if n:
                cnf.append([])
            return cnf

        for v in range(n):
            self._check_deadline(deadline)
            cnf.append([-y[v, k - 1]])
            for color in range(k - 1):
                self._check_deadline(deadline)
                cnf.append([y[v, color], -y[v, color + 1]])

            cnf.append([x[v, 0], y[v, 0]])
            cnf.append([-x[v, 0], -y[v, 0]])

            for color in range(1, k):
                self._check_deadline(deadline)
                cnf.append([-x[v, color], y[v, color - 1]])
                cnf.append([-x[v, color], -y[v, color]])
                cnf.append([x[v, color], -y[v, color - 1], y[v, color]])

        for u, v in edges:
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                cnf.append([-x[u, color], -x[v, color]])

        if self.symmetry_breaking:
            for v in range(min(n, k)):
                self._check_deadline(deadline)
                cnf.append([-y[v, v]])

            for v in range(1, n):
                self._check_deadline(deadline)
                for color in range(1, min(k, v + 1)):
                    self._check_deadline(deadline)
                    preceding_vertices = []
                    for u in range(color - 1, v):
                        self._check_deadline(deadline)
                        preceding_vertices.append(x[u, color - 1])
                    clause = [-x[v, color]] + preceding_vertices
                    cnf.append(clause)

        self._check_deadline(deadline)
        return cnf