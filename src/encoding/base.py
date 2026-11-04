from abc import ABC, abstractmethod
from typing import Any
from pysat.formula import CNF
from ..utils.graph_validation import validate_encoding_input

class CNFEncoding(ABC):
    @abstractmethod
    def encode(self, graph, k: int) -> CNF:
        """Convert graph coloring into a CNF formula."""
        pass

    def forbid_color(self, color: int) -> list[list[int]]:
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

    def release(self) -> None:
        self.x_vars = {}
        if hasattr(self, "y_vars"):
            self.y_vars = {}
        self._n = None
        self._k = None

class SolverEncoding(ABC):
    def __init__(self) -> None:
        self.x_vars: dict[tuple[int, int], Any] = {}
        self._n: int | None = None
        self._k: int | None = None

    @abstractmethod
    def encode(self, graph, k: int) -> Any:
        """Build and return the solver-native model."""
        raise NotImplementedError

    @abstractmethod
    def forbid_color(self, color: int) -> list[Any]:
        """Disable one color in the encoded model and return its constraints."""
        raise NotImplementedError

    @abstractmethod
    def decode_model(self, solution=None) -> list[int]:
        """Decode a feasible solver solution to one color per vertex."""
        raise NotImplementedError

    def _prepare(self, graph, k: int) -> tuple[int, set[tuple[int, int]]]:
        n, edges = validate_encoding_input(graph, k)
        self._n, self._k = n, k
        self.x_vars = {}
        return n, edges

    def _validate_color(self, color: int) -> None:
        if self._n is None or self._k is None:
            raise RuntimeError("encode() must be called before forbid_color()")
        if not isinstance(color, int) or isinstance(color, bool):
            raise TypeError("color must be an integer")
        if color < 0 or color >= self._k:
            raise ValueError("color must be in range of the encoded palette")

    def _require_encoded(self) -> None:
        if self._n is None or self._k is None:
            raise RuntimeError("encode() must be called before decode_model()")

    def release(self) -> None:
        self.x_vars = {}
        if hasattr(self, "y_vars"):
            self.y_vars = {}
        self._n = None
        self._k = None
        if hasattr(self, "color_vars"):
            self.color_vars = {}
        if hasattr(self, "model"):
            self.model = None


class ILPEncoding(SolverEncoding):
    pass