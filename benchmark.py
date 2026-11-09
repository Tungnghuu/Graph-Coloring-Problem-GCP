import argparse
import csv
import importlib.util
from pathlib import Path
from time import perf_counter

from src.chromatic_number.binarySearch_sat import BinarySearchSAT
from src.chromatic_number.bound_methods.combined import CombinedBounds
from src.chromatic_number.incremental_sat import IncrementalSAT
from src.chromatic_number.repeated_sat import RepeatedSAT
from src.encoding import (
    CPLEXCPEncoding,
    CPLEXMIPEncoding,
    GurobiILPEncoding,
    POHPEncoding,
    POPEncoding,
    SATEncoding,
)
from src.solver import CPLEXSolver, GurobiSolver, SATSolver
from src.utils.graph_io import read_col, sort_col_files_by_vertex_count
from src.utils.graph_validation import is_valid_coloring

try:
    import gurobipy
except ImportError:
    class _MissingGurobiError(Exception):
        pass

    GUROBI_ERROR = _MissingGurobiError
else:
    GUROBI_ERROR = gurobipy.GurobiError

try:
    from cplex.exceptions.errors import CplexSolverError
    from docplex.mp.utils import DOcplexLimitsExceeded
except ImportError:
    CPLEX_ERRORS = ()
else:
    CPLEX_ERRORS = (CplexSolverError, DOcplexLimitsExceeded)

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = "100_or_less"
DEFAULT_OUTPUT = PROJECT_DIR / "results" / "benchmark_summary.csv"

ENCODINGS = {
    "SAT": (SATEncoding, SATSolver),
    "POP": (POPEncoding, SATSolver),
    "POHP": (POHPEncoding, SATSolver),
    "Gurobi_ILP": (GurobiILPEncoding, GurobiSolver),
    "CPLEX_MIP": (CPLEXMIPEncoding, CPLEXSolver),
    "CPLEX_CP": (CPLEXCPEncoding, CPLEXSolver),
}
ENCODING_DEPENDENCIES = {
    "Gurobi_ILP": ("gurobipy",),
    "CPLEX_MIP": ("docplex.mp",),
    "CPLEX_CP": ("docplex.cp",),
}
METHODS = {
    "repeated": RepeatedSAT,
    "binary": BinarySearchSAT,
    "incremental": IncrementalSAT,
}
SUMMARY_FIELDS = [
    "graph", "vertices", "edges", "method", "encoding", "status",
    "chromatic_number", "valid_coloring", "bounds_time", "elapsed_time",
]


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def run_benchmark(
    dataset: str,
    methods: list[str],
    encoding_names: list[str],
    time_limit: float,
    output: Path,
    limit: int | None = None,
) -> None:
    dataset_dir = PROJECT_DIR / "data" / dataset
    graph_paths = sort_col_files_by_vertex_count(dataset_dir.glob("*.col"))
    if limit is not None:
        graph_paths = graph_paths[:limit]
    if not graph_paths:
        raise FileNotFoundError(f"No .col graph files found in {dataset_dir}")

    available_encodings = []
    for encoding_name in encoding_names:
        missing = [
            module
            for module in ENCODING_DEPENDENCIES.get(encoding_name, ())
            if not _module_available(module)
        ]
        if missing:
            print(
                f"Skipping {encoding_name}: missing package(s) "
                f"{', '.join(missing)}.",
                flush=True,
            )
        else:
            available_encodings.append(encoding_name)
    if not available_encodings:
        raise RuntimeError(
            "None of the selected encodings has its required dependencies "
            "installed."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for graph_path in graph_paths:
            graph = read_col(str(graph_path))
            bounds_start = perf_counter()
            bounds = CombinedBounds().find_bounds(graph)
            bounds_time = perf_counter() - bounds_start
            print(
                f"{graph_path.name}: {graph.n} vertices, "
                f"{len(graph.edges)} edges, bounds={bounds}",
                flush=True,
            )

            for method_name in methods:
                for encoding_name in available_encodings:
                    if method_name == "incremental" and encoding_name not in {
                        "SAT", "POP", "POHP"
                    }:
                        raise ValueError(
                            "incremental is only supported for CNF encodings: "
                            "SAT, POP, POHP"
                        )

                    encoding_type, solver_type = ENCODINGS[encoding_name]
                    encoding = encoding_type()
                    solver = METHODS[method_name]()
                    attempt_path = (
                        output.parent
                        / "attempts"
                        / f"{graph_path.stem}_{method_name}_{encoding_name}.csv"
                    )
                    start = perf_counter()
                    if encoding_name == "Gurobi_ILP":
                        try:
                            chromatic_number = solver.find_chromatic_number(
                                graph, encoding, bounds, str(attempt_path),
                                solver=solver_type(), time_limit=time_limit,
                                bounds_time=bounds_time,
                            )
                        except GUROBI_ERROR as error:
                            chromatic_number = None
                            solver.status = f"ERROR: {error}"
                            print(
                                f"  {method_name}/{encoding_name}: {solver.status}",
                                flush=True,
                            )
                    elif encoding_name in {"CPLEX_MIP", "CPLEX_CP"}:
                        try:
                            chromatic_number = solver.find_chromatic_number(
                                graph, encoding, bounds, str(attempt_path),
                                solver=solver_type(), time_limit=time_limit,
                                bounds_time=bounds_time,
                            )
                        except CPLEX_ERRORS as error:
                            chromatic_number = None
                            solver.status = f"ERROR: {error}"
                            print(
                                f"  {method_name}/{encoding_name}: {solver.status}",
                                flush=True,
                            )
                    elif method_name == "incremental":
                        chromatic_number = solver.find_chromatic_number(
                            graph, encoding, bounds, str(attempt_path),
                            time_limit=time_limit, bounds_time=bounds_time,
                        )
                    else:
                        chromatic_number = solver.find_chromatic_number(
                            graph, encoding, bounds, str(attempt_path),
                            solver=solver_type(), time_limit=time_limit,
                            bounds_time=bounds_time,
                        )
                    elapsed_time = perf_counter() - start
                    run_status = (
                        "SOLVED" if chromatic_number is not None else solver.status
                    )
                    writer.writerow({
                        "graph": graph_path.stem,
                        "vertices": graph.n,
                        "edges": len(graph.edges),
                        "method": method_name,
                        "encoding": encoding_name,
                        "status": run_status,
                        "chromatic_number": chromatic_number,
                        "valid_coloring": is_valid_coloring(graph),
                        "bounds_time": bounds_time,
                        "elapsed_time": elapsed_time,
                    })
                    file.flush()
                    print(
                        f"  {method_name}/{encoding_name}: "
                        f"k={chromatic_number}, status={run_status}",
                        flush=True,
                    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare graph-coloring methods and encodings."
    )
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument(
        "--methods", nargs="+", choices=sorted(METHODS), default=["repeated", "binary", "incremental"]
    )
    parser.add_argument(
        "--encodings", nargs="+", choices=sorted(ENCODINGS),
        default=["SAT", "POP", "POHP"],
    )
    parser.add_argument("--time-limit", type=float, default=30)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_benchmark(
        args.dataset, args.methods, args.encodings, args.time_limit,
        args.output, args.limit,
    )
