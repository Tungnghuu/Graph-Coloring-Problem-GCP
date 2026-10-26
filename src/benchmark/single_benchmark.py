from time import perf_counter
from ..solver.baseline import run_solver
from ..utils.graph_validation import is_valid_coloring

def run_benchmark(encoding, graph, k, solver_name="g3", time_limit=None):
    # Encoding time
    start = perf_counter()
    cnf = encoding.encode(graph, k)
    encoding_time = perf_counter() - start

    # CNF size
    num_variables = cnf.nv
    num_clauses = len(cnf.clauses)

    # Solving time
    start = perf_counter()
    satisfiable, model = run_solver(cnf, solver_name, time_limit)
    solving_time = perf_counter() - start
    timed_out = satisfiable is None

    # Decode and validate a SAT solution
    colors = None
    valid_coloring = None

    if satisfiable is True:
        colors = encoding.decode_model(model)
        graph.colors = colors
        valid_coloring = is_valid_coloring(graph)

    if timed_out:
        status = "TIMEOUT"
    else:
        status = "SAT" if satisfiable else "UNSAT"

    return {
        "k": k,
        "status": status,
        "num_variables": num_variables,
        "num_clauses": num_clauses,
        "encoding_time": encoding_time,
        "solving_time": solving_time,
        "total_time": encoding_time + solving_time,
        "valid_coloring": valid_coloring,
    }