from abc import ABC, abstractmethod

class LowerBoundMethod(ABC):
    @abstractmethod
    def find_lower_bound(self, graph) -> int:
        pass

class UpperBoundMethod(ABC):
    @abstractmethod
    def find_upper_bound(self, graph) -> int:
        pass

class BoundsMethod(LowerBoundMethod, UpperBoundMethod):
    pass
