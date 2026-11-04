from math import isfinite
from numbers import Real
from threading import Timer
from time import perf_counter

from pysat.solvers import Solver

from src.chromatic_number.base import ChromaticNumberSolver
from src.chromatic_number.results import ResultsWriter
from src.utils.graph_validation import is_valid_coloring

class IncrementalSAT(ChromaticNumberSolver):
    def __init__(self):
        self.best_k = None
        self.best_model = None
        self.status = None

    def find_chromatic_number(
        self, graph, encoding, bounds_method, results_path=None,
        *, solver_name="g3", time_limit=60, total_time_limit=None, bounds_time=0,
    ) -> int | None:
        
        self.best_k = None
        self.best_model = None
        self.status = None
        lower_bound, upper_bound = self._find_bounds(graph, bounds_method)
        self._validate_time_limit(time_limit)
        self._validate_time_limit(total_time_limit)
        self._validate_bounds_time(bounds_time)

        if not callable(getattr(encoding, "forbid_color", None)):
            raise TypeError("encoding must support forbid_color()")

        graph.colors = [None] * graph.n
        start = perf_counter()
        deadline = (
            start + total_time_limit
            if total_time_limit is not None
            else None
        )
        cnf = encoding.encode(graph, upper_bound)
        encoding_time = perf_counter() - start
        num_clauses = len(cnf.clauses)
        results = ResultsWriter(results_path) if results_path is not None else None

        # Variable IDs continue to refer to the original upper-bound palette.
        # Adding clauses preserves the validity of all previously learnt clauses.
        start = perf_counter()
        with Solver(name=solver_name, bootstrap_with=cnf.clauses) as solver:
            setup_time = perf_counter() - start
            first_attempt = True
            for k in range(upper_bound, lower_bound - 1, -1):
                if k < upper_bound:
                    start = perf_counter()
                    # Colors are zero-indexed: moving from k+1 to k forbids k.
                    clauses = encoding.forbid_color(k)
                    solver.append_formula(clauses)
                    num_clauses += len(clauses)
                    encoding_time = perf_counter() - start

                attempt_time_limit = time_limit
                if deadline is not None:
                    remaining_time = deadline - perf_counter()
                    if remaining_time <= 0:
                        self.status = "TIMEOUT"
                        break
                    if (
                        attempt_time_limit is None
                        or remaining_time < attempt_time_limit
                    ):
                        attempt_time_limit = remaining_time

                start = perf_counter()
                satisfiable = self._solve(solver, attempt_time_limit)
                solving_time = perf_counter() - start
                if k == upper_bound:
                    solving_time += setup_time
                self.status = (
                    "SAT" if satisfiable is True else
                    "UNSAT" if satisfiable is False else "TIMEOUT"
                )

                if satisfiable is True:
                    self.best_k = k
                    self.best_model = solver.get_model()
                    graph.colors = encoding.decode_model(self.best_model)
                valid_coloring = is_valid_coloring(graph)

                if results is not None:
                    results.save({
                        "method": "IncrementalSAT",
                        "encoding": encoding.__class__.__name__,
                        "k": k,
                        "status": self.status,
                        "num_variables": cnf.nv,
                        "num_clauses": num_clauses,
                        "valid_coloring": valid_coloring,
                        "bounds_time": bounds_time if first_attempt else 0,
                        "encoding_time": encoding_time,
                        "solving_time": solving_time,
                        "total_time": encoding_time + solving_time + (
                            bounds_time if first_attempt else 0
                        ),
                    })
                    first_attempt = False

                if satisfiable is None:
                    # Preserve the best feasible coloring found before timeout.
                    break
                if satisfiable is False:
                    break

        encoding.release()
        return self.best_k

    @staticmethod
    def _solve(solver, time_limit):
        if time_limit is None:
            return solver.solve()

        timer = Timer(time_limit, solver.interrupt)
        timer.daemon = True
        timer.start()
        try:
            return solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
            # Wait for an in-flight interrupt before clearing it or deleting
            # the solver, so it cannot interrupt the next SAT call by mistake.
            timer.join()
            solver.clear_interrupt()
