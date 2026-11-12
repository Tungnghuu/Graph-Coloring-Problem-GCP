from abc import ABC, abstractmethod
from typing import Any
from pysat.formula import CNF
from ..utils.graph_validation import (
    check_deadline,
    create_deadline,
    validate_encoding_input,
)

class CNFEncoding(ABC):
    @abstractmethod
    def encode(self, graph, k: int, *, time_limit=None) -> CNF:
        """Build a SAT formula for coloring the graph with k colors."""
        pass

    @staticmethod
    def _encoding_deadline(time_limit):
        return create_deadline(time_limit)

    @staticmethod
    def _check_deadline(deadline):
        check_deadline(deadline)

    def forbid_color(self, color: int) -> list[list[int]]:
        # The encoding must have created its variables before this method run
        has_variables = hasattr(self, "x_vars")
        has_vertex_count = getattr(self, "_n", None) is not None
        has_color_count = getattr(self, "_k", None) is not None
        if not has_variables or not has_vertex_count or not has_color_count:
            raise RuntimeError("encode() must be called before forbid_color()")

        color_is_integer = isinstance(color, int)
        color_is_boolean = isinstance(color, bool)
        if not color_is_integer or color_is_boolean:
            raise TypeError("color must be an integer")
        if color < 0 or color >= self._k:
            raise ValueError("color must be in range of the encoded palette")

        # Add one negative literal per vertex to forbid this color
        clauses = []
        for vertex in range(self._n):
            variable = self.x_vars[vertex, color]
            clauses.append([-variable])
        return clauses

    def decode_model(self, model: list[int]) -> list[int]:
        # Check that encoding was run first.
        if not hasattr(self, "x_vars"):
            raise RuntimeError("encode() must be called before decode_model()")

        if model is None:
            raise ValueError("cannot decode an absent or unsatisfiable model")

        # Keep only the variables that are true in the model
        true_vars = set()
        for var in model:
            if var > 0:
                true_vars.add(var)

        colors = []
        for vertex in range(self._n):
            assigned = []
            for color in range(self._k):
                variable = self.x_vars[vertex, color]
                if variable in true_vars:
                    assigned.append(color)

            if len(assigned) != 1:
                raise ValueError(
                    f"model must assign exactly one color to vertex {vertex}"
                )

            colors.append(assigned[0])
        return colors

    def release(self) -> None:
        # Clear variables so a later run starts with a clean encoding
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
    def encode(self, graph, k: int, *, time_limit=None) -> Any:
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

    @staticmethod
    def _encoding_deadline(time_limit):
        # Use the same time-limit handling as the SAT encodings
        return create_deadline(time_limit)

    @staticmethod
    def _check_deadline(deadline):
        # Use the same deadline check as the SAT encodings
        check_deadline(deadline)

    def _prepare(
        self, graph, k: int, *, deadline=None
    ) -> tuple[int, set[tuple[int, int]]]:
        n, edges = validate_encoding_input(graph, k, deadline=deadline)
        self._n, self._k = n, k
        self.x_vars = {}
        return n, edges

    def _validate_color(self, color: int) -> None:
        if self._n is None or self._k is None:
            raise RuntimeError("encode() must be called before forbid_color()")
        color_is_integer = isinstance(color, int)
        color_is_boolean = isinstance(color, bool)
        if not color_is_integer or color_is_boolean:
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