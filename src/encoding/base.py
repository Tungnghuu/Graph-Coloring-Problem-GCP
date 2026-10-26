from abc import ABC, abstractmethod
from pysat.formula import CNF

class Encoding(ABC):
    @abstractmethod
    def encode(self, graph, k: int) -> CNF:
        """Convert graph coloring into a CNF formula."""
        pass

    def decode_model(self, model: list[int]) -> list[int]:
        if not hasattr(self, "x_vars"):
            raise RuntimeError("encode() must be called before decode_model()")

        if model is None:
            raise ValueError("cannot decode an absent or unsatisfiable model")

        true_vars = set()

        for var in model:
            if var > 0:
                true_vars.add(var)

        colors = []

        for vertex in range(self._n):
            assigned = []

            for color in range(self._k):
                if self.x_vars[vertex, color] in true_vars:
                    assigned.append(color)

            if len(assigned) != 1:
                raise ValueError(
                    f"model must assign exactly one color to vertex {vertex}"
                )

            colors.append(assigned[0])

        return colors