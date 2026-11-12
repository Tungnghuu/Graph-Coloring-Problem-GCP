from time import perf_counter

from src.chromatic_number.base import ChromaticNumberSolver
from src.chromatic_number.results import ResultsWriter
from src.solver.baseline import SATSolver, Solver
from src.utils.graph_validation import is_valid_coloring

def run_sat_search(
    strategy,
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
) -> tuple[int | None, str | None]:
    if strategy not in ("binary", "repeated"):
        raise ValueError("strategy must be 'binary' or 'repeated'")

    lower_bound, upper_bound = ChromaticNumberSolver._find_bounds(
        graph, bounds_method
    )
    ChromaticNumberSolver._validate_time_limit(time_limit)
    ChromaticNumberSolver._validate_time_limit(encoding_time_limit)
    ChromaticNumberSolver._validate_time_limit(total_time_limit)
    ChromaticNumberSolver._validate_bounds_time(bounds_time)

    graph.colors = [None] * graph.n

    if solver is None:
        backend = SATSolver(solver_name=solver_name)
    else:
        backend = solver

    results = None
    if results_path is not None:
        results = ResultsWriter(results_path)

    deadline = None
    if total_time_limit is not None:
        deadline = perf_counter() + total_time_limit

    best_k = None
    status = None
    timed_out = False
    first_attempt = True
    low, high = lower_bound, upper_bound
    k = upper_bound

    while True:
        if strategy == "binary":
            if low > high:
                break
            k = (low + high) // 2
        else:
            if k < lower_bound:
                break

        model, encoding_time, encoded = ChromaticNumberSolver._encode(
            encoding, graph, k, encoding_time_limit, deadline
        )
        if not encoded:
            status = "TIMEOUT"
            if strategy == "binary":
                method_name = "BinarySearchSAT"
            else:
                method_name = "RepeatedSolver"

            if first_attempt:
                attempt_bounds_time = bounds_time
            else:
                attempt_bounds_time = 0

            ChromaticNumberSolver._record_encoding_timeout(
                results,
                method_name,
                encoding,
                k,
                attempt_bounds_time,
                encoding_time,
            )
            ChromaticNumberSolver._release_encoding(encoding, backend)
            break

        try:
            attempt_time_limit = time_limit
            if deadline is not None:
                remaining_time = deadline - perf_counter()
                if remaining_time <= 0:
                    status = "TIMEOUT"
                    timed_out = True
                    break
                if attempt_time_limit is None:
                    attempt_time_limit = remaining_time
                elif remaining_time < attempt_time_limit:
                    attempt_time_limit = remaining_time

            start = perf_counter()
            result = backend.solve(model, attempt_time_limit)
            solving_time = perf_counter() - start

            num_variables, num_constraints = backend.model_size(model)
            status = result.status
            if result.satisfiable is True:
                graph.colors = encoding.decode_model(result.solution)
            valid_coloring = is_valid_coloring(graph)

            if results is not None:
                if strategy == "binary":
                    method_name = "BinarySearchSAT"
                else:
                    method_name = "RepeatedSolver"

                if first_attempt:
                    attempt_bounds_time = bounds_time
                else:
                    attempt_bounds_time = 0

                total_time = encoding_time + solving_time
                if first_attempt:
                    total_time += bounds_time

                results.save({
                    "method": method_name,
                    "encoding": encoding.__class__.__name__,
                    "k": k,
                    "status": status,
                    "num_variables": num_variables,
                    "num_clauses": num_constraints,
                    "valid_coloring": valid_coloring,
                    "bounds_time": attempt_bounds_time,
                    "encoding_time": encoding_time,
                    "solving_time": solving_time,
                    "total_time": total_time,
                })
            first_attempt = False

            if result.satisfiable is True:
                best_k = k
                if strategy == "binary":
                    high = k - 1
            elif result.satisfiable is False:
                if strategy == "binary":
                    low = k + 1
                else:
                    break
            elif strategy == "binary":
                timed_out = True
                low = k + 1
            else:
                timed_out = True
                break
        finally:
            backend.close(model)
            encoding.release()

        if strategy == "repeated":
            k -= 1

    if timed_out:
        status = "TIMEOUT"
    return best_k, status