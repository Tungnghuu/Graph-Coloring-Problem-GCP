from abc import ABC, abstractmethod
from math import isfinite
from numbers import Real

class ChromaticNumberSolver(ABC):
    @abstractmethod
    def find_chromatic_number(self, graph, encoding, bounds_method):
        pass

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