from src.chromatic_number.base import ChromaticNumberSolver
from src.chromatic_number.sat_search import run_sat_search
from src.solver.baseline import Solver

class RepeatedSAT(ChromaticNumberSolver):
    def __init__(self) -> None:
        self.status = None

    def find_chromatic_number(
        self,
        graph,
        encoding,
        bounds_method,
        results_path=None,
        *,
        solver: Solver | None = None,
        solver_name: str = "g3",
        time_limit: float | None = 60,
        encoding_time_limit: float | None = 60,
        total_time_limit: float | None = None,
        bounds_time: float = 0,
    ) -> int | None:
        self.status = None
        result, self.status = run_sat_search(
            "repeated",
            graph,
            encoding,
            bounds_method,
            results_path,
            solver=solver,
            solver_name=solver_name,
            time_limit=time_limit,
            encoding_time_limit=encoding_time_limit,
            total_time_limit=total_time_limit,
            bounds_time=bounds_time,
        )
        return result