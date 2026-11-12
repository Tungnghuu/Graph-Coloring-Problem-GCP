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
from src.utils.graph_io import read_col
from src.utils.graph_validation import is_valid_coloring

PROJECT_DIR = Path(__file__).resolve().parents[2]

ALL_ENCODINGS = [
    ("SAT", SATEncoding, SATSolver),
    ("POP", POPEncoding, SATSolver),
    ("POHP", POHPEncoding, SATSolver),
    ("Gurobi_ILP", GurobiILPEncoding, GurobiSolver),
    ("CPLEX_MIP", CPLEXMIPEncoding, CPLEXSolver),
    ("CPLEX_CP", CPLEXCPEncoding, CPLEXSolver),
]

# Incremental search only works with the SAT encoding
INCREMENTAL_ENCODINGS = [
    ("SAT", SATEncoding, None),
    ("POP", POPEncoding, None),
    ("POHP", POHPEncoding, None),
]

def get_search_method(method_name):
    if method_name == "binary":
        return BinarySearchSAT()
    if method_name == "incremental":
        return IncrementalSAT()
    if method_name == "repeated":
        return RepeatedSAT()

    raise ValueError(f"Unknown search method: {method_name}")

def get_encodings(method_name, custom_encodings):
    if custom_encodings is not None:
        return custom_encodings

    if method_name == "incremental":
        return INCREMENTAL_ENCODINGS

    return ALL_ENCODINGS


def make_results_path(results_folder, graph_path, encoding_name, group_by_dataset):
    results_path = Path(results_folder)

    if group_by_dataset:
        results_path = results_path / graph_path.parent.name

    file_name = f"{graph_path.stem}_{encoding_name}_res.csv"
    return results_path / file_name


def print_result(
    graph_path, encoding_name, chromatic_number, solver, graph, results_path
):
    print(
        f"Graph: {graph_path.stem} | "
        f"Encoding: {encoding_name} | "
        f"Chromatic number: {chromatic_number} | "
        f"Status: {solver.status} | "
        f"Valid coloring: {is_valid_coloring(graph)} | ",
        flush=True,
    )

def run_one_encoding(
    method_name,
    graph,
    graph_path,
    bounds,
    bounds_time,
    encoding_details,
    results_path,
    time_limit,
    encoding_time_limit,
    total_time_limit,
):
    encoding_name, encoding_class, solver_class = encoding_details
    encoding = encoding_class()
    search_method = get_search_method(method_name)

    if solver_class is None:
        chromatic_number = search_method.find_chromatic_number(
            graph=graph,
            encoding=encoding,
            bounds_method=bounds,
            results_path=str(results_path),
            time_limit=time_limit,
            encoding_time_limit=encoding_time_limit,
            total_time_limit=total_time_limit,
            bounds_time=bounds_time,
        )
    else:
        backend = solver_class()
        chromatic_number = search_method.find_chromatic_number(
            graph=graph,
            encoding=encoding,
            bounds_method=bounds,
            results_path=str(results_path),
            solver=backend,
            time_limit=time_limit,
            encoding_time_limit=encoding_time_limit,
            total_time_limit=total_time_limit,
            bounds_time=bounds_time,
        )

    print_result(
        graph_path,
        encoding_name,
        chromatic_number,
        search_method,
        graph,
        results_path,
    )

def run_one_graph(
    graph_path,
    graph_number,
    graph_count,
    method_name,
    results_folder,
    time_limit,
    encoding_time_limit,
    total_time_limit,
    encoding_details,
    group_by_dataset,
):
    print(
        f"[{graph_number}/{graph_count}] Loading graph: {graph_path.name}",
        flush=True,
    )

    load_start = perf_counter()
    graph = read_col(str(graph_path))
    load_time = perf_counter() - load_start
    print(
        f"  Loaded {graph.n} vertices and {len(graph.edges)} edges "
        f"({load_time:.3f}s).",
        flush=True,
    )

    print("  Calculating bounds...", flush=True)
    bounds_start = perf_counter()
    bounds = CombinedBounds().find_bounds(graph)
    bounds_time = perf_counter() - bounds_start
    print(f"  Bounds: {bounds} ({bounds_time:.6f}s)", flush=True)

    for encoding_details_item in encoding_details:
        encoding_name = encoding_details_item[0]
        print(f"  Starting {encoding_name} encoding...", flush=True)

        results_path = make_results_path(
            results_folder,
            graph_path,
            encoding_name,
            group_by_dataset,
        )

        run_one_encoding(
            method_name,
            graph,
            graph_path,
            bounds,
            bounds_time,
            encoding_details_item,
            results_path,
            time_limit,
            encoding_time_limit,
            total_time_limit,
        )

def run_experiment(
    method_name,
    graph_paths,
    results_folder,
    time_limit=30,
    encoding_time_limit=30,
    total_time_limit=None,
    encoding_specs=None,
    group_results_by_dataset=True,
):
    is_known_method = (
        method_name == "binary"
        or method_name == "incremental"
        or method_name == "repeated"
    )
    if not is_known_method:
        raise ValueError(f"Unknown search method: {method_name}")

    graph_paths = list(graph_paths)
    if len(graph_paths) == 0:
        raise FileNotFoundError("No .col graph files found")

    print(f"Found {len(graph_paths)} graphs", flush=True)
    encodings_to_run = get_encodings(method_name, encoding_specs)

    for graph_number, graph_path in enumerate(graph_paths, start=1):
        graph_path = Path(graph_path)
        run_one_graph(
            graph_path,
            graph_number,
            len(graph_paths),
            method_name,
            results_folder,
            time_limit,
            encoding_time_limit,
            total_time_limit,
            encodings_to_run,
            group_results_by_dataset,
        )