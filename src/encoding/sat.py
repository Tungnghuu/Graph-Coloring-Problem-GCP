from pysat.formula import CNF
from .base import Encoding


class SATEncoding(Encoding):
    def encode(self, graph, k: int) -> CNF:
        cnf = CNF()

        # TODO: Build SAT clauses

        return cnf