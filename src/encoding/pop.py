from pysat.formula import CNF
from .base import CNFEncoding
from ..utils.graph_validation import validate_encoding_input

class POPEncoding(CNFEncoding):
    def __init__(self, symmetry_breaking: bool = True):
        self.symmetry_breaking = symmetry_breaking
        self.x_vars: dict[tuple[int, int], int] = {}
        self._n = None
        self._k = 0

    def encode(self, graph, k: int, *, time_limit=None) -> CNF:
        deadline = self._encoding_deadline(time_limit)
        n, edges = validate_encoding_input(graph, k, deadline=deadline)

        self._n, self._k = n, k
        self.x_vars = {}
        for v in range(n):
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                self.x_vars[v, color] = v * k + color + 1

        x = self.x_vars
        cnf = CNF()

        if k == 0:
            if n > 0:
                cnf.append([])
            return cnf

        # ALO: each vertex must have ALO color
        for v in range(n):
            self._check_deadline(deadline)
            variables = []
            for color in range(k):
                self._check_deadline(deadline)
                variables.append(x[v, color])
            cnf.append(variables)

        # Add clauses preventing a vertex from getting two colors
        for v in range(n):
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                for other_color in range(color + 1, k):
                    self._check_deadline(deadline)
                    cnf.append([-x[v, color], -x[v, other_color]])

        # Add clauses preventing connected vertices from sharing a color
        for u, v in edges:
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                cnf.append([-x[u, color], -x[v, color]])

        # Remove equivalent solutions with different color labels
        if self.symmetry_breaking:
            for v in range(min(n, k)):
                self._check_deadline(deadline)
                for color in range(v + 1, k):
                    self._check_deadline(deadline)
                    cnf.append([-x[v, color]])
        self._check_deadline(deadline)
        return cnf