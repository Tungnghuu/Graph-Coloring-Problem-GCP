from pathlib import Path
from time import perf_counter

from src.chromatic_number.binarySearch_sat import BinarySearchSAT
from src.chromatic_number.bound_methods.combined import CombinedBounds
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

PROJECT_DIR = Path(__file__).resolve().parent
INSTANCES_DIR = PROJECT_DIR / "data" / "instances"
RESULTS_DIR = PROJECT_DIR / "results" / "Binary" / "with_bm"
TIME_LIMIT = 30
TOTAL_TIME_LIMIT = None
ENCODINGS = (
    ("SAT", SATEncoding, SATSolver),
    ("POP", POPEncoding, SATSolver),
    ("POHP", POHPEncoding, SATSolver),
    ("Gurobi_ILP", GurobiILPEncoding, GurobiSolver),
    ("CPLEX_MIP", CPLEXMIPEncoding, CPLEXSolver),
    ("CPLEX_CP", CPLEXCPEncoding, CPLEXSolver),
)

def main():
    graph_paths = sort_col_files_by_vertex_count(INSTANCES_DIR.glob("*.col"))
    if not graph_paths:
        raise FileNotFoundError(f"No .col graph files found in {INSTANCES_DIR}")

    print(f"Found {len(graph_paths)} graphs in {INSTANCES_DIR}", flush=True)

    for graph_index, graph_path in enumerate(graph_paths, start=1):
        print(
            f"[{graph_index}/{len(graph_paths)}] Loading graph: {graph_path.name}",
            flush=True,
        )
        graph = read_col(str(graph_path))
        bounds_start = perf_counter()
        bounds = CombinedBounds().find_bounds(graph)
        bounds_time = perf_counter() - bounds_start
        print(f"  Bounds: {bounds} ({bounds_time:.6f}s)", flush=True)

        for encoding_name, encoding_type, solver_type in ENCODINGS:
            print(f"  Starting {encoding_name} encoding...", flush=True)
            encoding = encoding_type()
            results_path = (
                RESULTS_DIR / f"{graph_path.stem}_{encoding_name}_res.csv"
            )
            solver = BinarySearchSAT()

            chromatic_number = solver.find_chromatic_number(
                graph=graph,
                encoding=encoding,
                bounds_method=bounds,
                results_path=str(results_path),
                solver=solver_type(),
                time_limit=TIME_LIMIT,
                total_time_limit=TOTAL_TIME_LIMIT,
                bounds_time=bounds_time,
            )

            print(
                f"Graph: {graph_path.stem} | "
                f"Encoding: {encoding_name} | "
                f"Chromatic number: {chromatic_number} | "
                f"Status: {solver.status} | "
                f"Valid coloring: {is_valid_coloring(graph)} | "
                f"Results: {results_path.relative_to(PROJECT_DIR)}",
                flush=True,
            )

if __name__ == "__main__":
    main()
