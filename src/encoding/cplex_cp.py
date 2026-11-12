from typing import Any
from .base import SolverEncoding

class CPLEXCPEncoding(SolverEncoding):
    def __init__(self, symmetry_breaking: bool = True) -> None:
        super().__init__()
        self.symmetry_breaking = symmetry_breaking
        self.model: Any | None = None
        self.color_vars: dict[int, Any] = {}
        self._isolated_vertices: set[int] = set()
        self._forbidden_colors: set[int] = set()

    def encode(self, graph, k: int, *, time_limit=None) -> Any:
        try:
            import docplex.cp.model as cp
        except ImportError as error:
            raise ImportError(
                "CPLEXCPEncoding requires the docplex package"
            ) from error

        deadline = self._encoding_deadline(time_limit)
        n, edges = self._prepare(graph, k, deadline=deadline)
        self.model = cp.CpoModel(name="graph_coloring")

        incident_vertices = set()
        for edge in edges:
            self._check_deadline(deadline)
            incident_vertices.update(edge)

        self._isolated_vertices = set()
        for vertex in range(n):
            self._check_deadline(deadline)
            if vertex not in incident_vertices:
                self._isolated_vertices.add(vertex)

        self._forbidden_colors = set()
        self.color_vars = {}

        for vertex in range(n):
            self._check_deadline(deadline)
            if k > 0:
                self.color_vars[vertex] = cp.integer_var(
                    min=0, max=k - 1, name=f"color_{vertex}"
                )

        if k == 0 and n:
            self._check_deadline(deadline)
            self.model.add(cp.equal(0, 1))

        for u, v in edges:
            self._check_deadline(deadline)
            self.model.add(self.color_vars[u] != self.color_vars[v])

        if self.symmetry_breaking and n and k:
            self._check_deadline(deadline)
            self.model.add(self.color_vars[0] == 0)
            self._isolated_vertices.discard(0)

        self._check_deadline(deadline)
        return self.model

    def forbid_color(self, color: int) -> list[Any]:
        self._validate_color(color)
        if self.model is None:
            raise RuntimeError("encode() must be called before forbid_color()")

        constraints = []
        for vertex in range(self._n):
            constraint = self.color_vars[vertex] != color
            constraints.append(constraint)
        self.model.add(constraints)
        self._forbidden_colors.add(color)
        return constraints

    def decode_model(self, solution=None) -> list[int]:
        self._require_encoded()
        if self.model is None:
            raise RuntimeError("encode() must be called before decode_model()")
        if solution is None:
            raise ValueError("a feasible CP Optimizer solution is required")
        if not solution.is_solution():
            raise ValueError("cannot decode a CP Optimizer result without a solution")

        colors = []
        for vertex in range(self._n):
            try:
                color = solution.get_value(self.color_vars[vertex])
            except KeyError:
                if vertex not in self._isolated_vertices:
                    raise
                color = None
                for candidate in range(self._k):
                    if candidate not in self._forbidden_colors:
                        color = candidate
                        break
                if color is None:
                    raise ValueError(
                        f"solution omits isolated vertex {vertex}, "
                        "which has no available color"
                    ) from None
            if (
                not isinstance(color, int)
                or isinstance(color, bool)
                or not 0 <= color < self._k
            ):
                raise ValueError(
                    f"solution must assign a valid color to vertex {vertex}"
                )
            colors.append(color)
        return colors