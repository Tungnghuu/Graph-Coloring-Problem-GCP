"""Partial order coloring: y[v,c] means color(v) > c (zero based).

Core clauses (12a-d), Faber et al., SAT 2024, doi:10.4230/LIPIcs.SAT.2024.12.
Uses the vertex-index symmetry bound (13); no assignment variables.
"""
from pysat.formula import CNF
from .base import CNFEncoding
from ..utils.graph_validation import validate_encoding_input

class POPEncoding(CNFEncoding):
    def __init__(self, symmetry_breaking=True):
        self.symmetry_breaking = symmetry_breaking
        self.y_vars = {}
        self._n = self._k = None

    def encode(self, graph, k, *, time_limit=None):
        deadline = self._encoding_deadline(time_limit)
        n, edges = validate_encoding_input(graph, k, deadline=deadline)
        self._n, self._k = n, k
        self.y_vars = {}
        for v in range(n):
            for c in range(k):
                self._check_deadline(deadline)
                self.y_vars[v,c] = v*k+c+1
        y = self.y_vars
        cnf = CNF()
        if k == 0:
            if n: cnf.append([])
            return cnf
        for v in range(n):
            self._check_deadline(deadline)
            cnf.append([-y[v,k-1]])
            for c in range(k-1):
                self._check_deadline(deadline)
                cnf.append([y[v,c], -y[v,c+1]])
        for u,v in edges:
            cnf.append([y[u,0], y[v,0]])
            for c in range(1,k):
                self._check_deadline(deadline)
                cnf.append([-y[u,c-1], y[u,c], -y[v,c-1], y[v,c]])
        if self.symmetry_breaking:
            for v in range(min(n,k)):
                self._check_deadline(deadline)
                cnf.append([-y[v,v]])
        self._check_deadline(deadline)
        return cnf

    def decode_model(self, model):
        if self._n is None: raise RuntimeError('encode() must be called first')
        if model is None: raise ValueError('absent model')
        true = set(x for x in model if x > 0)
        colors = []
        for v in range(self._n):
            bits = [self.y_vars[v,c] in true for c in range(self._k)]
            if not bits or bits[-1] or bits != sorted(bits, reverse=True):
                raise ValueError('invalid partial order model')
            colors.append(sum(bits))
        return colors

    def forbid_color(self, color):
        if self._n is None: raise RuntimeError('encode() must be called first')
        if isinstance(color,bool) or not isinstance(color,int): raise TypeError('integer color required')
        if not 0 <= color < self._k: raise ValueError('color outside palette')
        # Forbid exactly this color; works independently of removal order.
        if color == 0: return [[self.y_vars[v,0]] for v in range(self._n)]
        return [[-self.y_vars[v,color-1], self.y_vars[v,color]] for v in range(self._n)]
