from typing import Any
from .base import ILPEncoding

class GurobiILPEncoding(ILPEncoding):
    def __init__(self, symmetry_breaking: bool = True) -> None:
        super().__init__()
        self.symmetry_breaking = symmetry_breaking
        self.model: Any | None = None

    def encode(self, graph, k: int) -> Any:
        try:
            import gurobipy as gp
        except ImportError as error:
            raise ImportError(
                "GurobiILPEncoding requires the gurobipy package"
            ) from error

        n, edges = self._prepare(graph, k)
        self._gp = gp
        self.model = gp.Model("graph_coloring")
        self.model.Params.OutputFlag = 0
        self.x_vars = {
            (vertex, color): self.model.addVar(
                vtype=gp.GRB.BINARY, name=f"x_{vertex}_{color}"
            )
            for vertex in range(n)
            for color in range(k)
        }

        if k == 0 and n:
            impossible = self.model.addVar(
                lb=0, ub=0, vtype=gp.GRB.CONTINUOUS, name="infeasible"
            )
            self.model.addConstr(impossible >= 1, name="no_available_color")

        if k:
            for vertex in range(n):
                self.model.addConstr(
                    gp.quicksum(
                        self.x_vars[vertex, color] for color in range(k)
                    )
                    == 1,
                    name=f"assign_{vertex}",
                )

        for u, v in edges:
            for color in range(k):
                self.model.addConstr(
                    self.x_vars[u, color] + self.x_vars[v, color] <= 1,
                    name=f"edge_{u}_{v}_color_{color}",
                )

        if self.symmetry_breaking:
            for vertex in range(min(n, k)):
                for color in range(vertex + 1, k):
                    self.model.addConstr(
                        self.x_vars[vertex, color] == 0,
                        name=f"symmetry_{vertex}_{color}",
                    )

        self.model.update()
        return self.model

    def forbid_color(self, color: int) -> list[Any]:
        self._validate_color(color)
        if self.model is None:
            raise RuntimeError("encode() must be called before forbid_color()")
        return [
            self.model.addConstr(
                self.x_vars[vertex, color] == 0,
                name=f"forbid_color_{vertex}_{color}",
            )
            for vertex in range(self._n)
        ]

    def decode_model(self, solution=None) -> list[int]:
        self._require_encoded()
        model = self.model if solution is None else solution
        if model is None or model is not self.model:
            raise ValueError("solution must be the encoded Gurobi model")
        if model.SolCount == 0:
            raise ValueError("cannot decode a model without a feasible solution")

        colors = []
        for vertex in range(self._n):
            assigned = [
                color
                for color in range(self._k)
                if self.x_vars[vertex, color].X > 0.5
            ]
            if len(assigned) != 1:
                raise ValueError(
                    f"solution must assign exactly one color to vertex {vertex}"
                )
            colors.append(assigned[0])
        return colors