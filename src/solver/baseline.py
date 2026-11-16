from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import isfinite
from numbers import Real
from threading import Timer
from typing import Any
from time import perf_counter

from pysat.formula import CNF
from pysat.solvers import Solver as PySATSolver

@dataclass(frozen=True)
class SolveResult:
    satisfiable: bool | None
    solution: Any = None
    timed_out: bool = False
    backend_status: str = ""
    setup_time: float | None = None
    solving_time: float | None = None

    @property
    def status(self) -> str:
        if self.satisfiable is True:
            return "SAT"
        if self.satisfiable is False:
            return "UNSAT"
        return "TIMEOUT" if self.timed_out else "UNKNOWN"

class Solver(ABC):
    @abstractmethod
    def solve(self, model: Any, time_limit: float | None = None) -> SolveResult:
        raise NotImplementedError

    @abstractmethod
    def model_size(self, model: Any) -> tuple[int, int]:
        """Return the number of variables and constraints in a model."""
        raise NotImplementedError

    def close(self, _model: Any) -> None:
        """Release backend resources associated with a solved model."""
        del _model

    @staticmethod
    def validate_time_limit(time_limit: float | None) -> None:
        if time_limit is not None:
            is_boolean = isinstance(time_limit, bool)
            is_number = isinstance(time_limit, Real)
            if is_boolean or not is_number:
                raise TypeError("time_limit must be a number of seconds or None")

            is_finite = isfinite(time_limit)
            if not is_finite or time_limit <= 0:
                raise ValueError("time_limit must be a positive finite number")

class SATSolver(Solver):
    """PySAT backend for CNF encodings."""

    def __init__(self, solver_name: str = "g3") -> None:
        self.solver_name = solver_name

    def solve(
        self, model: CNF, time_limit: float | None = None
    ) -> SolveResult:
        if not isinstance(model, CNF):
            raise TypeError("SATSolver requires a PySAT CNF model")
        self.validate_time_limit(time_limit)

        setup_start = perf_counter()
        with PySATSolver(
            name=self.solver_name, bootstrap_with=model.clauses
        ) as solver:
            setup_time = perf_counter() - setup_start
            solve_start = perf_counter()
            if time_limit is None:
                satisfiable = solver.solve()
            else:
                # Interrupt the solver after the requested time limit
                timer = Timer(time_limit, solver.interrupt)
                timer.daemon = True
                timer.start()
                try:
                    satisfiable = solver.solve_limited(expect_interrupt=True)
                finally:
                    timer.cancel()
                    timer.join()
                    solver.clear_interrupt()

            solving_time = perf_counter() - solve_start
            solution = None
            if satisfiable is True:
                solution = solver.get_model()

        return SolveResult(satisfiable=satisfiable, solution=solution, timed_out=satisfiable is None,
                           backend_status="interrupted" if satisfiable is None else "finished",
                           setup_time=setup_time, solving_time=solving_time)

    def model_size(self, model: CNF) -> tuple[int, int]:
        if not isinstance(model, CNF):
            raise TypeError("SATSolver requires a PySAT CNF model")
        return model.nv, len(model.clauses)

class GurobiSolver(Solver):
    def solve(self, model: Any, time_limit: float | None = None) -> SolveResult:
        self.validate_time_limit(time_limit)
        try:
            import gurobipy as gp
        except ImportError as error:
            raise ImportError("Requires the gurobipy package") from error

        if not isinstance(model, gp.Model):
            raise TypeError("GurobiSolver requires a gurobipy Model")
        if time_limit is not None:
            model.Params.TimeLimit = time_limit

        model.Params.Threads = 1
        model.optimize()
        if model.SolCount > 0:
            return SolveResult(satisfiable=True, solution=model, timed_out=model.Status == gp.GRB.TIME_LIMIT, backend_status=str(model.Status))
        if model.Status == gp.GRB.INFEASIBLE:
            return SolveResult(satisfiable=False)
        return SolveResult(satisfiable=None, timed_out=model.Status == gp.GRB.TIME_LIMIT, backend_status=str(model.Status))

    def model_size(self, model: Any) -> tuple[int, int]:
        try:
            import gurobipy as gp
        except ImportError as error:
            raise ImportError("GurobiSolver requires the gurobipy package") from error
        if not isinstance(model, gp.Model):
            raise TypeError("GurobiSolver requires a gurobipy Model")
        model.update()
        return model.NumVars, model.NumConstrs

    def close(self, model: Any) -> None:
        try:
            import gurobipy as gp
        except ImportError as error:
            raise ImportError("GurobiSolver requires the gurobipy package") from error
        if not isinstance(model, gp.Model):
            raise TypeError("GurobiSolver requires a gurobipy Model")
        model.dispose()

class CPLEXMIPSolver(Solver):
    def solve(self, model: Any, time_limit: float | None = None) -> SolveResult:
        self.validate_time_limit(time_limit)
        try:
            from docplex.mp.model import Model
        except ImportError as error:
            raise ImportError(
                "CPLEXILPSolver requires the docplex package"
            ) from error

        if not isinstance(model, Model):
            raise TypeError("CPLEXILPSolver requires a DOcplex MP Model")
        if time_limit is not None:
            model.parameters.timelimit = time_limit

        model.parameters.threads = 1
        solution = model.solve(log_output=False)
        status = model.solve_details.status.lower()
        timed_out = "time limit" in status
        if solution is not None:
            return SolveResult(satisfiable=True, solution=solution, timed_out=timed_out, backend_status=status)
        if status in ("infeasible", "integer infeasible"):
            return SolveResult(satisfiable=False)
        return SolveResult(satisfiable=None, timed_out=timed_out, backend_status=status)

    def model_size(self, model: Any) -> tuple[int, int]:
        try:
            from docplex.mp.model import Model
        except ImportError as error:
            raise ImportError(
                "CPLEXILPSolver requires the docplex package"
            ) from error
        if not isinstance(model, Model):
            raise TypeError("CPLEXILPSolver requires a DOcplex MP Model")
        return model.number_of_variables, model.number_of_constraints

    def close(self, model: Any) -> None:
        try:
            from docplex.mp.model import Model
        except ImportError as error:
            raise ImportError(
                "CPLEXILPSolver requires the docplex package"
            ) from error
        if not isinstance(model, Model):
            raise TypeError("CPLEXILPSolver requires a DOcplex MP Model")
        model.end()

class CPLEXCPSolver(Solver):
    def solve(self, model: Any, time_limit: float | None = None) -> SolveResult:
        self.validate_time_limit(time_limit)
        try:
            from docplex.cp.model import CpoModel
        except ImportError as error:
            raise ImportError(
                "CPLEXCPSolver requires the docplex package"
            ) from error

        if not isinstance(model, CpoModel):
            raise TypeError("CPLEXCPSolver requires a DOcplex CP model")

        options = {"LogVerbosity": "Quiet", "Workers": 1}
        if time_limit is not None:
            options["TimeLimit"] = time_limit

        solution = model.solve(**options)
        status = solution.get_solve_status().lower()
        stop = str(solution.get_stop_cause())
        timed_out = "time" in stop.lower() or (stop == "SearchStoppedByLimit" and time_limit is not None)
        if solution.is_solution():
            return SolveResult(satisfiable=True, solution=solution, timed_out=timed_out, backend_status=status+":"+stop)
        if status in ("infeasible", "integer infeasible"):
            return SolveResult(satisfiable=False)
        return SolveResult(satisfiable=None, timed_out=timed_out, backend_status=status+":"+stop)

    def model_size(self, model: Any) -> tuple[int, int]:
        try:
            from docplex.cp.model import CpoModel
        except ImportError as error:
            raise ImportError(
                "CPLEXCPSolver requires the docplex package"
            ) from error
        if not isinstance(model, CpoModel):
            raise TypeError("CPLEXCPSolver requires a DOcplex CP model")
        stats = model.get_statistics()
        return (
            stats.get_number_of_variables(),
            stats.get_number_of_constraints(),
        )

class CPLEXSolver(Solver):
    @staticmethod
    def _select_backend(model: Any) -> Solver:
        try:
            from docplex.cp.model import CpoModel
            from docplex.mp.model import Model
        except ImportError as error:
            raise ImportError("CPLEXSolver requires the docplex package") from error

        if isinstance(model, CpoModel):
            return CPLEXCPSolver()
        if isinstance(model, Model):
            return CPLEXMIPSolver()
        raise TypeError("CPLEXSolver requires a DOcplex MP or CP model")

    def solve(self, model: Any, time_limit: float | None = None) -> SolveResult:
        backend = self._select_backend(model)
        return backend.solve(model, time_limit)

    def model_size(self, model: Any) -> tuple[int, int]:
        backend = self._select_backend(model)
        return backend.model_size(model)

    def close(self, model: Any) -> None:
        backend = self._select_backend(model)
        backend.close(model)

def run_solver(
    cnf: CNF,
    solver_name: str = "g3",
    time_limit: float | None = None,
) -> tuple[bool | None, list[int] | None]:
    # Keep the older helper while using the shared SAT solver class.
    result = SATSolver(solver_name=solver_name).solve(cnf, time_limit)
    return result.satisfiable, result.solution