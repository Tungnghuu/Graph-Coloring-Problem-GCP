from math import isfinite
from numbers import Real
from time import perf_counter

from src.chromatic_number.base import ChromaticNumberSolver
from src.chromatic_number.results import ResultsWriter
from src.solver.baseline import run_solver


class RepeatedSAT(ChromaticNumberSolver):
    def __init__(self):
        self.status = None

    def find_chromatic_number(
        self,
        graph,
        encoding,
        bounds_method,
        results_path,
        *,
        solver_name="g3",
        time_limit=60,
        total_time_limit=None,
        bounds_time=0,
    ):
        self.status = None
        lower_bound, upper_bound = self._find_bounds(graph, bounds_method)
        self._validate_time_limit(time_limit)
        self._validate_time_limit(total_time_limit)
        self._validate_bounds_time(bounds_time)
        results = ResultsWriter(results_path)
        best_k = None
        deadline = (
            perf_counter() + total_time_limit
            if total_time_limit is not None
            else None
        )

        first_attempt = True
        for k in range(upper_bound, lower_bound - 1, -1):
            start = perf_counter()
            cnf = encoding.encode(graph, k)
            enc_time = perf_counter() - start

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
            satisfiable, _ = run_solver(
                cnf,
                solver_name=solver_name,
                time_limit=attempt_time_limit,
            )
            solv_time = perf_counter() - start

            self.status = (
                "SAT" if satisfiable is True else
                "UNSAT" if satisfiable is False else "TIMEOUT"
            )

            results.save({
                "method": "RepeatedSAT",
                "encoding": encoding.__class__.__name__,
                "k": k,
                "status": self.status,
                "num_variables": cnf.nv,
                "num_clauses": len(cnf.clauses),
                "bounds_time": bounds_time if first_attempt else 0,
                "encoding_time": enc_time,
                "solving_time": solv_time,
                "total_time": enc_time + solv_time + (
                    bounds_time if first_attempt else 0
                ),
            })
            first_attempt = False

            if satisfiable is True:
                best_k = k
            elif satisfiable is False:
                break
            else:
                break
        return best_k

    @staticmethod
    def _validate_time_limit(time_limit):
        if time_limit is not None:
            if isinstance(time_limit, bool) or not isinstance(time_limit, Real):
                raise TypeError("time_limit must be a number of seconds or None")
            if not isfinite(time_limit) or time_limit <= 0:
                raise ValueError("time_limit must be a positive finite number")

    @staticmethod
    def _validate_bounds_time(bounds_time):
        if isinstance(bounds_time, bool) or not isinstance(bounds_time, Real):
            raise TypeError("bounds_time must be a non-negative number of seconds")
        if not isfinite(bounds_time) or bounds_time < 0:
            raise ValueError("bounds_time must be a non-negative finite number")

    @staticmethod
    def _find_bounds(graph, bounds_method):
        if callable(getattr(bounds_method, "find_bounds", None)):
            bounds = bounds_method.find_bounds(graph)
        elif (
            callable(getattr(bounds_method, "find_lower_bound", None))
            and callable(getattr(bounds_method, "find_upper_bound", None))
        ):
            bounds = (
                bounds_method.find_lower_bound(graph),
                bounds_method.find_upper_bound(graph),
            )
        else:
            bounds = bounds_method

        try:
            lower, upper = bounds
        except (TypeError, ValueError) as error:
            raise ValueError("bounds must contain a lower and an upper bound") from error
        if any(isinstance(b, bool) or not isinstance(b, int) for b in (lower, upper)):
            raise TypeError("bounds must be integers")
        if not 0 <= lower <= upper:
            raise ValueError("bounds must satisfy 0 <= lower <= upper")
        return lower, upper