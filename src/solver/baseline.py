from math import isfinite
from numbers import Real
from threading import Timer

from pysat.formula import CNF
from pysat.solvers import Solver


def run_solver(cnf: CNF, solver_name: str = "g3", time_limit: float | None = None) -> tuple[bool | None, list[int] | None]:
    if time_limit is not None:
        if isinstance(time_limit, bool) or not isinstance(time_limit, Real):
            raise TypeError("time_limit must be a number of seconds or None")

        if not isfinite(time_limit) or time_limit <= 0:
            raise ValueError("time_limit must be a positive finite number")

    with Solver(name=solver_name, bootstrap_with=cnf.clauses) as solver:
        if time_limit is None:
            satisfiable = solver.solve()

        else:
            timer = Timer(time_limit, solver.interrupt)
            timer.daemon = True
            timer.start()

            try:
                satisfiable = solver.solve_limited(
                    expect_interrupt=True
                )
            finally:
                timer.cancel()
                solver.clear_interrupt()

        model = solver.get_model() if satisfiable is True else None

    return satisfiable, model