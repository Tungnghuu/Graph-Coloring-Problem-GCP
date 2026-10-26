from time import perf_counter
from src.chromatic_number.base import ChromaticNumberSolver
from src.chromatic_number.results import ResultsWriter
from src.solver.baseline import run_solver

class RepeatedSAT(ChromaticNumberSolver):
    def find_chromatic_number(self, graph, encoding, bounds_method, results_path,):
        lower_bound, upper_bound = bounds_method
        results = ResultsWriter(results_path)

        best_k = None

        for k in range(upper_bound, lower_bound - 1, -1):
            # Encode
            start = perf_counter()
            cnf = encoding.encode(graph, k)
            enc_time = perf_counter() - start

            # Solve
            start = perf_counter()
            satisfiable, model = run_solver(cnf, solver_name = "g3", time_limit = 60)
            solv_time = perf_counter() - start

            if satisfiable is True:
                status = "SAT"
            elif satisfiable is False:
                status = "UNSAT"
            else: status = "TIMEOUT"

            # Save every attempt, including UNSAT
            results.save({
                "method": "RepeatedSAT",
                "encoding": encoding.__class__.__name__,
                "k": k,
                "status": status,
                "num_variables": cnf.nv,
                "num_clauses": len(cnf.clauses),
                "encoding_time": enc_time,
                "solving_time": solv_time,
                "total_time": enc_time + solv_time,
            })

            if satisfiable:
                best_k = k
            else:
                # The previous SAT result is optimal
                break
        return best_k