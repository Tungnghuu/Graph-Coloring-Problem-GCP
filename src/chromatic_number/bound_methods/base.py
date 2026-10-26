from abc import ABC, abstractmethod

class BoundsMethod(ABC):
    @abstractmethod
    def find_lower_bound(self, graph) -> int:
        pass

    @abstractmethod
    def find_upper_bound(self, graph) -> int:
        pass
