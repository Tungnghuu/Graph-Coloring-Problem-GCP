from abc import ABC, abstractmethod
from math import isfinite
from numbers import Real
from time import perf_counter
from src.utils.graph_validation import effective_time_limit

class ChromaticNumberSolver(ABC):
    @abstractmethod
    def find_chromatic_number(self, graph, encoding, bounds_method):
        pass

    @staticmethod
    def _find_bounds(graph, bounds_method):
        find_bounds = getattr(bounds_method, "find_bounds", None)
        find_lower_bound = getattr(bounds_method, "find_lower_bound", None)
        find_upper_bound = getattr(bounds_method, "find_upper_bound", None)

        if callable(find_bounds):
            bounds = bounds_method.find_bounds(graph)
        elif callable(find_lower_bound) and callable(find_upper_bound):
            lower_bound = find_lower_bound(graph)
            upper_bound = find_upper_bound(graph)
            bounds = (lower_bound, upper_bound)
        else:
            bounds = bounds_method

        try:
            lower, upper = bounds
        except (TypeError, ValueError) as error:
            raise ValueError("bounds must contain a lower and an upper bound") from error

        lower_is_invalid = isinstance(lower, bool) or not isinstance(lower, int)
        upper_is_invalid = isinstance(upper, bool) or not isinstance(upper, int)
        if lower_is_invalid or upper_is_invalid:
            raise TypeError("bounds must be integers")

        if not 0 <= lower <= upper:
            raise ValueError("bounds must satisfy 0 <= lower <= upper")

        return lower, upper

    @staticmethod
    def _validate_time_limit(time_limit):
        if time_limit is not None:
            is_boolean = isinstance(time_limit, bool)
            is_number = isinstance(time_limit, Real)
            if is_boolean or not is_number:
                raise TypeError("time_limit must be a number of seconds or None")
            is_finite = isfinite(time_limit)
            if not is_finite or time_limit <= 0:
                raise ValueError("time_limit must be a positive finite number")

    @staticmethod
    def _validate_bounds_time(bounds_time):
        is_boolean = isinstance(bounds_time, bool)
        is_number = isinstance(bounds_time, Real)
        if is_boolean or not is_number:
            raise TypeError("bounds_time must be a non-negative number of seconds")
        is_finite = isfinite(bounds_time)
        if not is_finite or bounds_time < 0:
            raise ValueError("bounds_time must be a non-negative finite number")

    @staticmethod
    def _effective_time_limit(time_limit, deadline):
        return effective_time_limit(time_limit, deadline)

    @classmethod
    def _encode(cls, encoding, graph, k, time_limit, deadline):
        start = perf_counter()
        try:
            model = encoding.encode(
                graph,
                k,
                time_limit=cls._effective_time_limit(time_limit, deadline),
            )
        except TimeoutError:
            return None, perf_counter() - start, False
        return model, perf_counter() - start, True

    @staticmethod
    def _record_encoding_timeout(
        results, method, encoding, k, bounds_time, encoding_time
    ):
        if results is not None:
            results.save({
                "method": method,
                "encoding": encoding.__class__.__name__,
                "k": k,
                "status": "TIMEOUT",
                "num_variables": 0,
                "num_clauses": 0,
                "valid_coloring": False,
                "bounds_time": bounds_time,
                "encoding_time": encoding_time,
                "solving_time": 0,
                "total_time": encoding_time + bounds_time,
            })

    @staticmethod
    def _release_encoding(encoding, backend=None):
        model = getattr(encoding, "model", None)
        if backend is not None and model is not None:
            backend.close(model)
        encoding.release()