import argparse
import csv
import json
from pathlib import Path
import sys
from time import perf_counter

from src.benchmark.experiment_runner import get_search_method, ALL_ENCODINGS
from src.chromatic_number.bound_methods.combined import CombinedBounds
from src.chromatic_number.results import ResultsWriter
from src.chromatic_number.base import ChromaticNumberSolver as Base
from src.solver.baseline import SATSolver
from src.encoding import POHPEncoding
from src.utils.graph_io import read_col
from src.utils.graph_validation import is_valid_coloring

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

def sweep(graph_path, out, ks, solve_limit, encoding_limit):
    graph = read_col(graph_path)
    backend = SATSolver('g3')
    output_directory = out
    color_counts = ks

    graph_output_directory = output_directory / graph_path.parent.name
    result_path = graph_output_directory / (
        graph_path.stem + '_POHP_k_sweep.csv'
    )
    if result_path.exists():
        raise FileExistsError(result_path)

    metadata = {
        'solver': 'g3',
        'time_limit': solve_limit,
        'encoding_time_limit': encoding_limit,
        'total_time_limit': None,
        'symmetry_breaking': True,
        'parameters': 'one worker; other backend defaults',
        'graph': str(graph_path),
        'experiment': 'independent Repeated POHP k sweep',
    }
    writer = ResultsWriter(result_path, metadata)
    any_attempt_timed_out = False

    try:
        # Build and solve a fresh encoded model for every requested color count.
        for color_count in color_counts:
            encoding = POHPEncoding()
            attempt_start_time = perf_counter()

            model, encoding_time, encoding_succeeded = Base._encode(
                encoding,
                graph,
                color_count,
                encoding_limit,
                None,
            )

            # Record an encoding timeout and continue to the next k value.
            if not encoding_succeeded:
                Base._record_encoding_timeout(
                    writer,
                    'RepeatedSolver',
                    encoding,
                    color_count,
                    0,
                    encoding_time,
                )
                any_attempt_timed_out = True
                encoding.release()
                continue

            try:
                # Ask the SAT backend to solve the model for this k value.
                result = backend.solve(model, solve_limit)

                # Clear colors from a previous attempt before decoding this result.
                graph.colors = [None] * graph.n
                if result.satisfiable is True:
                    graph.colors = encoding.decode_model(result.solution)

                # Confirm that the decoded coloring really colors every graph edge.
                if result.satisfiable is True:
                    coloring_is_valid = is_valid_coloring(graph)
                else:
                    coloring_is_valid = False

                if result.satisfiable is True and not coloring_is_valid:
                    raise ValueError('invalid coloring')

                # Save model size and timing measurements for this independent solve.
                variable_count, clause_count = backend.model_size(model)
                attempt_record = {
                    'method': 'RepeatedSolver',
                    'encoding': 'POHPEncoding',
                    'k': color_count,
                    'status': result.status,
                    'num_variables': variable_count,
                    'num_clauses': clause_count,
                    'valid_coloring': coloring_is_valid,
                    'bounds_time': 0,
                    'encoding_time': encoding_time,
                    'setup_time': result.setup_time,
                    'solving_time': result.solving_time,
                    'total_time': perf_counter() - attempt_start_time,
                    'solver_called': True,
                    'timed_out': result.timed_out,
                    'timeout_phase': (
                        'solving' if result.timed_out else ''
                    ),
                    'backend_status': result.backend_status,
                }
                writer.save(attempt_record)
                any_attempt_timed_out = (
                    any_attempt_timed_out or result.timed_out
                )
            finally:
                # Free this solver model and encoding before the next k value.
                backend.close(model)
                encoding.release()

        if any_attempt_timed_out:
            completion_status = 'Timeout'
        else:
            completion_status = 'Completed'

        writer.finish(
            completion=completion_status,
            lower_bound=None,
            best_k=None,
            reason='requested_k_range_finished',
        )
    except Exception as error:
        # Record the failure in the manifest and then let the caller see it.
        writer.finish(
            completion='Error',
            lower_bound=None,
            best_k=None,
            reason=str(error),
        )
        raise

    return result_path

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Run graph-coloring benchmarks and optional k sweeps.'
    )
    parser.add_argument(
        '--graph',
        type=Path,
        action='append',
        default=[],
        help='Graph file to process; this option can be repeated.',
    )
    parser.add_argument(
        '--representatives',
        type=Path,
        help='CSV with path,k_min,k_max; one graph per bucket.',
    )
    parser.add_argument('--sweep-only', action='store_true')
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='New directory, separate from historical results.',
    )
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--solve-limit', type=float, default=30)
    parser.add_argument('--encoding-limit', type=float, default=30)
    parser.add_argument('--run-limit', type=float, default=120)
    parser.add_argument('--sweep', action='store_true')
    parser.add_argument('--k-min', type=int)
    parser.add_argument('--k-max', type=int)

    parsed_arguments = parser.parse_args()
    return parser, parsed_arguments

def main():
    parser, args = parse_arguments()
    k_ranges_by_graph = {}

    if args.representatives:
        with args.representatives.open() as manifest_file:
            manifest_rows = csv.DictReader(manifest_file)
            for row in manifest_rows:
                graph_path = Path(row['path'])
                args.graph.append(graph_path)
                k_ranges_by_graph[str(graph_path)] = (
                    int(row['k_min']),
                    int(row['k_max']),
                )

    if not args.graph:
        parser.error('provide --graph or --representatives')

    if args.output.exists():
        parser.error(
            'output must be a new directory; existing results are preserved'
        )

    args.output.mkdir(parents=True)

    expected_runs = []
    experiment_errors = []

    for path in args.graph:
        graph = read_col(path)
        bounds_start_time = perf_counter()
        bounds = CombinedBounds().find_bounds(graph)
        bounds_time = perf_counter() - bounds_start_time

        if args.sweep or args.sweep_only:
            if args.k_min is not None:
                minimum_k = args.k_min
            else:
                minimum_k = max(1, bounds[0] - 2)

            if args.k_max is not None:
                maximum_k = args.k_max
            else:
                maximum_k = min(graph.n, bounds[1] + 2)

            if str(path) in k_ranges_by_graph:
                minimum_k, maximum_k = k_ranges_by_graph[str(path)]

            if minimum_k > maximum_k:
                parser.error('k-min must be <= k-max')

            sweep(
                path,
                args.output / 'exp',
                range(minimum_k, maximum_k + 1),
                args.solve_limit,
                args.encoding_limit,
            )

        if args.sweep_only:
            continue

        for method in ('Repeated', 'Binary', 'Incremental'):
            for encoding_name, encoding_class, solver_class in ALL_ENCODINGS:
                is_sat_encoding = encoding_name in ('SAT', 'POP', 'POHP')
                if not is_sat_encoding:
                    if not args.native or method == 'Incremental':
                        continue

                result_path = (
                    args.output
                    / method
                    / path.parent.name
                    / (path.stem + '_' + encoding_name + '_res.csv')
                )
                expected_runs.append({
                    'graph_id': path.parent.name + '/' + path.name,
                    'graph': path.stem,
                    'group': path.parent.name,
                    'method': method,
                    'encoding': encoding_name,
                })

                try:
                    solver_options = {
                        'time_limit': args.solve_limit,
                        'encoding_time_limit': args.encoding_limit,
                        'total_time_limit': args.run_limit,
                        'bounds_time': bounds_time,
                    }

                    if method != 'Incremental':
                        solver_options['solver'] = solver_class()

                    search_method = get_search_method(method.lower())
                    search_method.find_chromatic_number(
                        graph,
                        encoding_class(),
                        bounds,
                        result_path,
                        **solver_options,
                    )
                except Exception as error:
                    experiment_errors.append({
                        'graph': str(path),
                        'method': method,
                        'encoding': encoding_name,
                        'error': repr(error),
                    })

    expected_manifest_path = args.output.with_suffix('.expected.csv')
    expected_fields = [
        'graph_id',
        'graph',
        'group',
        'method',
        'encoding',
    ]
    with expected_manifest_path.open('w', newline='') as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=expected_fields,
        )
        writer.writeheader()
        writer.writerows(expected_runs)

    error_report_path = args.output.with_suffix('.errors.json')
    error_report_path.write_text(
        json.dumps(experiment_errors, indent=2)
    )

    print(
        f'Expected runs: {len(expected_runs)}; '
        f'errors: {len(experiment_errors)}; '
        f'manifest: {expected_manifest_path}'
    )
    if experiment_errors:
        print(json.dumps(experiment_errors, indent=2))

if __name__ == '__main__':
    main()