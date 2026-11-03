from abc import ABC, abstractmethod
from pysat.formula import CNF

class Encoding(ABC):
    @abstractmethod
    def encode(self, graph, k: int) -> CNF:
        """Convert graph coloring into a CNF formula."""
        pass

    def forbid_color(self, color: int) -> list[list[int]]:
        """Return unit clauses disabling a color in the current encoding.

        Incremental search encodes its upper bound once, then adds these
        clauses as it removes the highest remaining color. Variable IDs and
        the original palette size stay unchanged, so models remain decodable.
        Encodings using this helper must expose one-hot ``x_vars[v, color]``
        and preserve valid colorings when the highest colors are disabled.
        """
        if (
            not hasattr(self, "x_vars")
            or getattr(self, "_n", None) is None
            or getattr(self, "_k", None) is None
        ):
            raise RuntimeError("encode() must be called before forbid_color()")

        if not isinstance(color, int) or isinstance(color, bool):
            raise TypeError("color must be an integer")
        if color < 0 or color >= self._k:
            raise ValueError("color must be in range of the encoded palette")

        return [[-self.x_vars[vertex, color]] for vertex in range(self._n)]

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
