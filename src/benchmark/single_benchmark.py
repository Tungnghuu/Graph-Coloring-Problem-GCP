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
    """Benchmark a compatible encoding/solver pair.

    ``solver_name`` preserves the original PySAT API. Pass a solver strategy
    for Gurobi or CPLEX models.
    """
    start = perf_counter()
    model = encoding.encode(graph, k)
    encoding_time = perf_counter() - start

    solver = solver or SATSolver(solver_name=solver_name)
    graph.colors = [None] * graph.n
    result = None
    try:
        num_variables, num_constraints = solver.model_size(model)
        start = perf_counter()
        result = solver.solve(model, time_limit)
        solving_time = perf_counter() - start

        if result.satisfiable is True:
            graph.colors = encoding.decode_model(result.solution)
        valid_coloring = is_valid_coloring(graph)

        return {
            "k": k,
            "status": result.status,
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
        model = None
        result = None
