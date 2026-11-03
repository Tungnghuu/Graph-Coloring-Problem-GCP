from pysat.formula import CNF
from .base import Encoding
from ..utils.graph_validation import validate_encoding_input

class SATEncoding(Encoding):
    """Direct one-hot encoding of graph coloring."""
    def __init__(self, symmetry_breaking = False):
        self.symmetry_breaking = symmetry_breaking
        self.x_vars = {}
        self._n = None
        self._k = None

    def encode(self, graph, k: int) -> CNF:
        n, edges = validate_encoding_input(graph, k)
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

        if self.symmetry_breaking:
            # A canonical relabeling gives vertex v a color no greater than v.
            for v in range(min(n, k)):
                for color in range(v + 1, k):
                    cnf.append([-self.x_vars[v, color]])
        return cnf
