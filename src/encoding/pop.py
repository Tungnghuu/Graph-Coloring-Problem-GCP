from pysat.formula import CNF
from .base import Encoding


class POPEncoding(Encoding):
    def encode(self, graph, k: int) -> CNF:
        cnf = CNF()

        # TODO: Build POP clauses

        return cnf