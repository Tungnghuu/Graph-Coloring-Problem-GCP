from abc import ABC, abstractmethod

class ChromaticNumberSolver(ABC):
    @abstractmethod
    def find_chromatic_number(self, graph, encoding, bounds_method):
        pass