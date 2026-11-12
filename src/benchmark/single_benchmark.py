from time import perf_counter

from ..solver.baseline import SATSolver, Solver
from ..utils.graph_validation import is_valid_coloring

def run_benchmark(
    encoding,
    graph,
    k,
    solver_name="g3",
    time_limit=None,
    *,
    solver: Solver | None = None,
):

    start = perf_counter()
    model = encoding.encode(graph, k)
    encoding_time = perf_counter() - start

    if solver is None:
        solver = SATSolver(solver_name=solver_name)

    graph.colors = [None] * graph.n

    try:
        num_variables, num_constraints = solver.model_size(model)
        start = perf_counter()
        solve_result = solver.solve(model, time_limit)
        solving_time = perf_counter() - start

        if solve_result.satisfiable is True:
            graph.colors = encoding.decode_model(solve_result.solution)

        valid_coloring = is_valid_coloring(graph)

        return {
            "k": k,
            "status": solve_result.status,
            "num_variables": num_variables,
            "num_clauses": num_constraints,
            "encoding_time": encoding_time,
            "solving_time": solving_time,
            "total_time": encoding_time + solving_time,
            "valid_coloring": valid_coloring,
        }
    finally:
        solver.close(model)
        encoding.release()
