from pysat.formula import CNF
from .base import Encoding


class POHPEncoding(Encoding):
    def encode(self, graph, k: int) -> CNF:
        cnf = CNF()

        # TODO: Build POHP clauses

        return cnf