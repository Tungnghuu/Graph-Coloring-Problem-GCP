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
        self,
        graph,
        encoding,
        bounds_method,
        results_path=None,
        *,
        solver_name="g3",
        time_limit=60,
        encoding_time_limit=60,
        total_time_limit=None,
        bounds_time=0,
    ) -> int | None:
        self.best_k = None
        self.best_model = None
        self.status = None

        lower_bound, upper_bound = self._find_bounds(graph, bounds_method)
        self._validate_time_limit(time_limit)
        self._validate_time_limit(encoding_time_limit)
        self._validate_time_limit(total_time_limit)
        self._validate_bounds_time(bounds_time)

        if not callable(getattr(encoding, "forbid_color", None)):
            raise TypeError("encoding must support forbid_color()")

        graph.colors = [None] * graph.n
        start = perf_counter()
        deadline = None
        if total_time_limit is not None:
            deadline = start + total_time_limit

        results = None
        if results_path is not None:
            results = ResultsWriter(results_path)

        cnf, encoding_time, encoded = self._encode(
            encoding, graph, upper_bound, encoding_time_limit, deadline
        )
        if not encoded:
            self.status = "TIMEOUT"
            self._record_encoding_timeout(
                results,
                "IncrementalSAT",
                encoding,
                upper_bound,
                bounds_time,
                encoding_time,
            )
            self._release_encoding(encoding)
            return self.best_k

        num_clauses = len(cnf.clauses)

        start = perf_counter()
        with Solver(name=solver_name, bootstrap_with=cnf.clauses) as solver:
            setup_time = perf_counter() - start
            first_attempt = True

            for k in range(upper_bound, lower_bound - 1, -1):
                if k < upper_bound:
                    start = perf_counter()
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
                    if attempt_time_limit is None:
                        attempt_time_limit = remaining_time
                    elif remaining_time < attempt_time_limit:
                        attempt_time_limit = remaining_time

                start = perf_counter()
                satisfiable = self._solve(solver, attempt_time_limit)
                solving_time = perf_counter() - start

                if k == upper_bound:
                    solving_time += setup_time

                if satisfiable is True:
                    self.status = "SAT"
                elif satisfiable is False:
                    self.status = "UNSAT"
                else:
                    self.status = "TIMEOUT"

                if satisfiable is True:
                    self.best_k = k
                    self.best_model = solver.get_model()
                    graph.colors = encoding.decode_model(self.best_model)

                valid_coloring = is_valid_coloring(graph)

                if results is not None:
                    if first_attempt:
                        attempt_bounds_time = bounds_time
                    else:
                        attempt_bounds_time = 0

                    total_time = encoding_time + solving_time
                    if first_attempt:
                        total_time += bounds_time

                    results.save({
                        "method": "IncrementalSAT",
                        "encoding": encoding.__class__.__name__,
                        "k": k,
                        "status": self.status,
                        "num_variables": cnf.nv,
                        "num_clauses": num_clauses,
                        "valid_coloring": valid_coloring,
                        "bounds_time": attempt_bounds_time,
                        "encoding_time": encoding_time,
                        "solving_time": solving_time,
                        "total_time": total_time,
                    })
                    first_attempt = False

                if satisfiable is None:
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
            timer.join()
            solver.clear_interrupt()