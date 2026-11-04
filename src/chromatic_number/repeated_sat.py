from time import perf_counter

from src.chromatic_number.base import ChromaticNumberSolver
from src.chromatic_number.results import ResultsWriter
from src.solver.baseline import SATSolver, Solver
from src.utils.graph_validation import is_valid_coloring

class RepeatedSAT(ChromaticNumberSolver):
    def __init__(self) -> None:
        self.status = None

    def find_chromatic_number(
        self, graph, encoding, bounds_method, results_path=None,
        *, solver: Solver | None = None, solver_name: str = "g3", time_limit: float | None = 60,
        total_time_limit: float | None = None,
        bounds_time: float = 0,
    ) -> int | None:
        self.status = None
        lower_bound, upper_bound = self._find_bounds(graph, bounds_method)
        self._validate_time_limit(time_limit)
        self._validate_time_limit(total_time_limit)
        self._validate_bounds_time(bounds_time)

        graph.colors = [None] * graph.n
        backend = solver or SATSolver(solver_name=solver_name)
        results = ResultsWriter(results_path) if results_path is not None else None
        deadline = (
            perf_counter() + total_time_limit
            if total_time_limit is not None
            else None
        )
        best_k = None
        first_attempt = True
        for k in range(upper_bound, lower_bound - 1, -1):
            start = perf_counter()
            model = encoding.encode(graph, k)
            encoding_time = perf_counter() - start

            result = None
            try:
                attempt_time_limit = time_limit
                if deadline is not None:
                    remaining_time = deadline - perf_counter()
                    if remaining_time <= 0:
                        self.status = "TIMEOUT"
                        return best_k
                    if (
                        attempt_time_limit is None
                        or remaining_time < attempt_time_limit
                    ):
                        attempt_time_limit = remaining_time

                start = perf_counter()
                result = backend.solve(model, attempt_time_limit)
                solving_time = perf_counter() - start
                num_variables, num_constraints = backend.model_size(model)
                self.status = result.status
                if result.satisfiable is True:
                    graph.colors = encoding.decode_model(result.solution)
                valid_coloring = is_valid_coloring(graph)

                if results is not None:
                    results.save({
                        "method": "RepeatedSolver",
                        "encoding": encoding.__class__.__name__,
                        "k": k,
                        "status": self.status,
                        "num_variables": num_variables,
                        "num_clauses": num_constraints,
                        "valid_coloring": valid_coloring,
                        "bounds_time": bounds_time if first_attempt else 0,
                        "encoding_time": encoding_time,
                        "solving_time": solving_time,
                        "total_time": encoding_time + solving_time + (
                            bounds_time if first_attempt else 0
                        ),
                    })
                first_attempt = False

                if result.satisfiable is True:
                    best_k = k
                elif result.satisfiable is False:
                    break
                else:
                    break
            finally:
                backend.close(model)
                encoding.release()
                model = None
                result = None

        return best_k