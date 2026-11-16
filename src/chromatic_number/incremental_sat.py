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

        bound_start = perf_counter()
        lower_bound, upper_bound = self._find_bounds(graph, bounds_method)
        if hasattr(bounds_method,"find_bounds") or hasattr(bounds_method,"find_lower_bound"):
            bounds_time += perf_counter() - bound_start
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
            results = ResultsWriter(results_path, dict(initial_lb=lower_bound, initial_ub=upper_bound,
                bounds_time=bounds_time, solver=solver_name, time_limit=time_limit,
                encoding_time_limit=encoding_time_limit, total_time_limit=total_time_limit,
                symmetry_breaking=getattr(encoding,"symmetry_breaking",None),
                timing="SAT: separate setup/solve; native: backend call includes native overhead", parameters="one worker; other backend defaults"))

        # Logging/environment collection is outside the search budget.
        deadline = perf_counter() + total_time_limit if total_time_limit else None
        try:
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
                    phase="total" if deadline is not None and perf_counter()>=deadline else "encoding",
                )
                self._release_encoding(encoding)
                if results: results.finish(completion="Timeout", lower_bound=lower_bound, best_k=self.best_k, reason="encoding_or_total_limit")
                return self.best_k

            num_clauses = len(cnf.clauses)

            start = perf_counter()
            with Solver(name=solver_name, bootstrap_with=cnf.clauses) as solver:
                setup_time = perf_counter() - start
                first_attempt = True
                update_time = 0

                for k in range(upper_bound, lower_bound - 1, -1):
                    if k < upper_bound:
                        start = perf_counter()
                        clauses = encoding.forbid_color(k)
                        encoding_time = perf_counter() - start
                        start = perf_counter()
                        solver.append_formula(clauses)
                        update_time = perf_counter() - start
                        num_clauses += len(clauses)

                    attempt_time_limit = time_limit
                    if deadline is not None:
                        remaining_time = deadline - perf_counter()
                        if remaining_time <= 0:
                            self.status = "TIMEOUT"
                            if results: results.save(dict(method="IncrementalSAT", encoding=type(encoding).__name__,
                                k=k,status="TIMEOUT",solver_called=False,timed_out=True,timeout_phase="total",
                                encoding_time=encoding_time,setup_time=setup_time if first_attempt else update_time,
                                solving_time=0,num_variables=cnf.nv,num_clauses=num_clauses,
                                total_time=encoding_time+(setup_time if first_attempt else update_time)+(bounds_time if first_attempt else 0),
                                bounds_time=bounds_time if first_attempt else 0))
                            break
                        if attempt_time_limit is None:
                            attempt_time_limit = remaining_time
                        elif remaining_time < attempt_time_limit:
                            attempt_time_limit = remaining_time

                    start = perf_counter()
                    satisfiable = self._solve(solver, attempt_time_limit)
                    solving_time = perf_counter() - start

                    attempt_setup = setup_time if first_attempt else update_time

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
                    if satisfiable is True and not valid_coloring:
                        raise ValueError("backend returned invalid coloring")

                    if results is not None:
                        if first_attempt:
                            attempt_bounds_time = bounds_time
                        else:
                            attempt_bounds_time = 0

                        total_time = encoding_time + solving_time + attempt_setup
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
                            "setup_time": attempt_setup,
                            "solver_called": True,
                            "timed_out": satisfiable is None,
                            "timeout_phase": "solving" if satisfiable is None else "",
                            "best_k": self.best_k,
                            "total_time": total_time,
                        })
                        first_attempt = False

                    if satisfiable is None:
                        break
                    if satisfiable is False:
                        lower_bound = max(lower_bound, k+1)
                        break

            encoding.release()
            if results: results.finish(completion="Timeout" if self.status=="TIMEOUT" else "Completed",
                lower_bound=lower_bound,best_k=self.best_k,reason="time_limit" if self.status=="TIMEOUT" else "search_exhausted")
            return self.best_k
        except Exception as error:
            if results: results.finish(completion="Error", lower_bound=lower_bound, best_k=self.best_k, reason=type(error).__name__+": "+str(error))
            raise
        finally:
            encoding.release()

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
