from pysat.formula import CNF
from .base import CNFEncoding
from ..utils.graph_validation import validate_encoding_input

class SATEncoding(CNFEncoding):
    def __init__(self, symmetry_breaking=True):
        self.symmetry_breaking = symmetry_breaking
        self.x_vars = {}
        self._n = None
        self._k = None

    def encode(self, graph, k: int, *, time_limit=None) -> CNF:
        deadline = self._encoding_deadline(time_limit)
        n, edges = validate_encoding_input(graph, k, deadline=deadline)
        self._n, self._k = n, k

        self.x_vars = {}
        for vertex in range(n):
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                self.x_vars[vertex, color] = vertex * k + color + 1

        cnf = CNF()

        if k == 0:
            if n:
                cnf.append([])
            return cnf

        # Every vertex must get at least one color and cannot get two colors
        for vertex in range(n):
            self._check_deadline(deadline)
            variables = []
            for color in range(k):
                self._check_deadline(deadline)
                variables.append(self.x_vars[vertex, color])
            cnf.append(variables)
            for index, variable in enumerate(variables):
                self._check_deadline(deadline)
                for other in range(index + 1, len(variables)):
                    self._check_deadline(deadline)
                    cnf.append([-variable, -variables[other]])

        # Neighboring vertices cannot use the same color
        for u, v in edges:
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                cnf.append([-self.x_vars[u, color], -self.x_vars[v, color]])

        # Remove equivalent solutions that only differ by color labels
        if self.symmetry_breaking:
            # A canonical relabeling gives vertex v a color no greater than v
            for v in range(min(n, k)):
                self._check_deadline(deadline)
                for color in range(v + 1, k):
                    self._check_deadline(deadline)
                    cnf.append([-self.x_vars[v, color]])
        self._check_deadline(deadline)
        return cnf