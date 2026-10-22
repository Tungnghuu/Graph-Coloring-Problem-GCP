from abc import ABC, abstractmethod
from pysat.formula import CNF


class Encoding(ABC):
    @abstractmethod
    def encode(self, graph, k: int) -> CNF:
        """Convert graph coloring into a CNF formula."""
        pass