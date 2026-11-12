from typing import Any
from .base import ILPEncoding

class GurobiILPEncoding(ILPEncoding):
    def __init__(self, symmetry_breaking: bool = True) -> None:
        super().__init__()
        self.symmetry_breaking = symmetry_breaking
        self.model: Any | None = None

    def encode(self, graph, k: int, *, time_limit=None) -> Any:
        try:
            import gurobipy as gp
        except ImportError as error:
            raise ImportError(
                "GurobiILPEncoding requires the gurobipy package"
            ) from error

        deadline = self._encoding_deadline(time_limit)
        n, edges = self._prepare(graph, k, deadline=deadline)
        self._gp = gp
        self.model = gp.Model("graph_coloring")
        self.model.Params.OutputFlag = 0
        # Create one binary variable for every vertex/color pair.
        for vertex in range(n):
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                self.x_vars[vertex, color] = self.model.addVar(
                    vtype=gp.GRB.BINARY, name=f"x_{vertex}_{color}"
                )

        if k == 0 and n:
            impossible = self.model.addVar(
                lb=0, ub=0, vtype=gp.GRB.CONTINUOUS, name="infeasible"
            )
            self.model.addConstr(impossible >= 1, name="no_available_color")

        if k:
            for vertex in range(n):
                self._check_deadline(deadline)
                variables = []
                for color in range(k):
                    self._check_deadline(deadline)
                    variables.append(self.x_vars[vertex, color])
                self.model.addConstr(
                    gp.quicksum(variables) == 1,
                    name=f"assign_{vertex}",
                )

        for u, v in edges:
            self._check_deadline(deadline)
            for color in range(k):
                self._check_deadline(deadline)
                self.model.addConstr(
                    self.x_vars[u, color] + self.x_vars[v, color] <= 1,
                    name=f"edge_{u}_{v}_color_{color}",
                )

        if self.symmetry_breaking:
            for vertex in range(min(n, k)):
                self._check_deadline(deadline)
                for color in range(vertex + 1, k):
                    self._check_deadline(deadline)
                    self.model.addConstr(
                        self.x_vars[vertex, color] == 0,
                        name=f"symmetry_{vertex}_{color}",
                    )

        self._check_deadline(deadline)
        self.model.update()
        return self.model

    def forbid_color(self, color: int) -> list[Any]:
        self._validate_color(color)
        if self.model is None:
            raise RuntimeError("encode() must be called before forbid_color()")

        constraints = []
        for vertex in range(self._n):
            constraint = self.model.addConstr(
                self.x_vars[vertex, color] == 0,
                name=f"forbid_color_{vertex}_{color}",
            )
            constraints.append(constraint)
        return constraints

    def decode_model(self, solution=None) -> list[int]:
        self._require_encoded()
        if solution is None:
            model = self.model
        else:
            model = solution

        if model is None or model is not self.model:
            raise ValueError("solution must be the encoded Gurobi model")
        if model.SolCount == 0:
            raise ValueError("cannot decode a model without a feasible solution")

        colors = []
        for vertex in range(self._n):
            assigned = []
            for color in range(self._k):
                variable = self.x_vars[vertex, color]
                if variable.X > 0.5:
                    assigned.append(color)
            if len(assigned) != 1:
                raise ValueError(
                    f"solution must assign exactly one color to vertex {vertex}"
                )
            colors.append(assigned[0])
        return colors