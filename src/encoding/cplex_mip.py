from typing import Any
from .base import ILPEncoding

class CPLEXMIPEncoding(ILPEncoding):
    def __init__(self, symmetry_breaking: bool = True) -> None:
        super().__init__()
        self.symmetry_breaking = symmetry_breaking
        self.model: Any | None = None

    def encode(self, graph, k: int) -> Any:
        try:
            from docplex.mp.model import Model
        except ImportError as error:
            raise ImportError(
                "CPLEXILPEncoding requires the docplex package"
            ) from error

        n, edges = self._prepare(graph, k)
        self.model = Model(name="graph_coloring", log_output=False)
        self.x_vars = {
            (vertex, color): self.model.binary_var(
                name=f"x_{vertex}_{color}"
            )
            for vertex in range(n)
            for color in range(k)
        }

        if k == 0 and n:
            impossible = self.model.continuous_var(
                lb=0, ub=0, name="infeasible"
            )
            self.model.add_constraint(impossible >= 1, "no_available_color")

        if k:
            for vertex in range(n):
                self.model.add_constraint(
                    self.model.sum(
                        self.x_vars[vertex, color] for color in range(k)
                    )
                    == 1,
                    f"assign_{vertex}",
                )

        for u, v in edges:
            for color in range(k):
                self.model.add_constraint(
                    self.x_vars[u, color] + self.x_vars[v, color] <= 1,
                    f"edge_{u}_{v}_color_{color}",
                )

        if self.symmetry_breaking:
            for vertex in range(min(n, k)):
                for color in range(vertex + 1, k):
                    self.model.add_constraint(
                        self.x_vars[vertex, color] == 0,
                        f"symmetry_{vertex}_{color}",
                    )

        return self.model

    def forbid_color(self, color: int) -> list[Any]:
        self._validate_color(color)
        if self.model is None:
            raise RuntimeError("encode() must be called before forbid_color()")
        return [
            self.model.add_constraint(
                self.x_vars[vertex, color] == 0,
                f"forbid_color_{vertex}_{color}",
            )
            for vertex in range(self._n)
        ]

    def decode_model(self, solution=None) -> list[int]:
        self._require_encoded()
        if self.model is None:
            raise RuntimeError("encode() must be called before decode_model()")
        solution = self.model.solution if solution is None else solution
        if solution is None:
            raise ValueError("cannot decode a model without a feasible solution")

        colors = []
        for vertex in range(self._n):
            assigned = [
                color
                for color in range(self._k)
                if solution.get_value(self.x_vars[vertex, color]) > 0.5
            ]
            if len(assigned) != 1:
                raise ValueError(
                    f"solution must assign exactly one color to vertex {vertex}"
                )
            colors.append(assigned[0])
        return colors