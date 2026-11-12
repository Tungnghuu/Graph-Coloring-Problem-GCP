from typing import Any
from .base import ILPEncoding

class CPLEXMIPEncoding(ILPEncoding):
    def __init__(self, symmetry_breaking: bool = True) -> None:
        super().__init__()
        self.symmetry_breaking = symmetry_breaking
        self.model: Any | None = None

    def encode(self, graph, k: int, *, time_limit=None) -> Any:
        try:
            from docplex.mp.model import Model
        except ImportError as error:
            raise ImportError(
                "CPLEXILPEncoding requires the docplex package"
            ) from error

        deadline = self._encoding_deadline(time_limit)
        n, edges = self._prepare(graph, k, deadline=deadline)
        self.model = Model(name="graph_coloring", log_output=False)

        for vertex in range(n):
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                self.x_vars[vertex, color] = self.model.binary_var(
                    name=f"x_{vertex}_{color}"
                )

        if k == 0 and n:
            impossible = self.model.continuous_var(
                lb=0, ub=0, name="infeasible"
            )
            self.model.add_constraint(impossible >= 1, "no_available_color")

        if k:
            for vertex in range(n):
                self._check_deadline(deadline)
                variables = []
                for color in range(k):
                    self._check_deadline(deadline)
                    variables.append(self.x_vars[vertex, color])
                self.model.add_constraint(
                    self.model.sum(variables) == 1,
                    f"assign_{vertex}",
                )

        for u, v in edges:
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                self.model.add_constraint(
                    self.x_vars[u, color] + self.x_vars[v, color] <= 1,
                    f"edge_{u}_{v}_color_{color}",
                )

        if self.symmetry_breaking:
            for vertex in range(min(n, k)):
                self._check_deadline(deadline)
                for color in range(vertex + 1, k):
                    self._check_deadline(deadline)
                    self.model.add_constraint(
                        self.x_vars[vertex, color] == 0,
                        f"symmetry_{vertex}_{color}",
                    )

        self._check_deadline(deadline)
        return self.model

    def forbid_color(self, color: int) -> list[Any]:
        self._validate_color(color)
        if self.model is None:
            raise RuntimeError("encode() must be called before forbid_color()")

        constraints = []
        for vertex in range(self._n):
            constraint = self.model.add_constraint(
                self.x_vars[vertex, color] == 0,
                f"forbid_color_{vertex}_{color}",
            )
            constraints.append(constraint)
        return constraints

    def decode_model(self, solution=None) -> list[int]:
        self._require_encoded()
        if self.model is None:
            raise RuntimeError("encode() must be called before decode_model()")
        if solution is None:
            solution = self.model.solution
        if solution is None:
            raise ValueError("cannot decode a model without a feasible solution")

        colors = []
        for vertex in range(self._n):
            assigned = []
            for color in range(self._k):
                variable = self.x_vars[vertex, color]
                if solution.get_value(variable) > 0.5:
                    assigned.append(color)

            if len(assigned) != 1:
                raise ValueError(
                    f"solution must assign exactly one color to vertex {vertex}"
                )
            colors.append(assigned[0])
        return colors