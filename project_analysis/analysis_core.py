from pathlib import Path
from collections import defaultdict
import csv
import math
import statistics

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent

ENCODINGS = (
    'SAT',
    'POP',
    'POHP',
    'Gurobi_ILP',
    'CPLEX_MIP',
    'CPLEX_CP',
)

METHODS = {
    'RepeatedSolver': 'Repeated',
    'RepeatedSAT': 'Repeated',
    'IncrementalSAT': 'Incremental',
    'BinarySearchSAT': 'Binary',
}

FIELDS = [
    'source', 'run_id', 'graph', 'graph_id', 'group', 'vertices', 'edges',
    'method', 'encoding', 'backend', 'config_id', 'comparison_config',
    'metadata_verified', 'completion', 'termination_reason', 'attempts',
    'solver_calls', 'best_k', 'lower_bound', 'gap', 'proof', 'timeout',
    'timeout_phase', 'encoding_time', 'setup_time', 'solving_time',
    'bounds_time', 'recorded_time', 'total_time', 'time_basis',
    'num_variables', 'num_clauses', 'first_k', 'quality',
]

ATTEMPT_FIELDS = [
    'source', 'graph', 'graph_id', 'group', 'vertices', 'edges', 'method',
    'encoding', 'backend', 'k', 'status', 'num_variables', 'num_clauses',
    'valid_coloring', 'bounds_time', 'encoding_time', 'setup_time',
    'solving_time', 'total_time', 'solver_called', 'timed_out',
    'timeout_phase', 'best_k', 'backend_status',
]

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open('w', newline='', encoding='utf-8') as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=fields,
            extrasaction='ignore',
        )
        writer.writeheader()
        writer.writerows(rows)

def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as input_file:
        return list(csv.DictReader(input_file))

def number(value):
    try:
        converted_value = float(value)
        if math.isfinite(converted_value):
            return converted_value
        return None
    except (ValueError, TypeError):
        return None

def integer(value):
    converted_value = number(value)
    if converted_value is None:
        return None
    if not converted_value.is_integer():
        return None
    return int(converted_value)

def flag(value):
    if isinstance(value, bool):
        return value

    text_value = str(value).lower()
    known_values = {
        'true': True,
        'false': False,
    }
    return known_values.get(text_value)

def load_runs(out=ROOT / 'processed'):
    output_directory = out
    run_rows = read_csv(output_directory / 'summary_runs.csv')
    numeric_fields = (
        'vertices', 'edges', 'attempts', 'solver_calls',
        'best_k', 'lower_bound', 'gap', 'encoding_time', 'setup_time',
        'solving_time',  'bounds_time', 'recorded_time', 'total_time',
        'num_variables', 'num_clauses', 'first_k',
    )
    boolean_fields = ('timeout', 'metadata_verified')

    for run in run_rows:
        for field in numeric_fields:
            run[field] = number(run.get(field))

        for field in boolean_fields:
            run[field] = flag(run.get(field)) is True

    return run_rows

def clean_runs(rows):
    fatal_quality_flags = (
        'contradictory_bounds',
        'identity_mismatch',
        'invalid_rows',
        'graph_unresolved',
        'repeated_configuration',
        'repeated_bounds_time',
        'invalid_coloring',
    )
    cleaned_rows = []

    for row in rows:
        has_required_identity = (
            row['graph']
            and row['group']
            and row['method']
            and row['encoding'] in ENCODINGS
        )
        is_complete_enough = row['completion'] not in ('Missing', 'Error')
        has_fatal_quality_flag = any(
            quality_flag in (row['quality'] or '')
            for quality_flag in fatal_quality_flags
        )

        if (
            has_required_identity
            and is_complete_enough
            and not has_fatal_quality_flag
        ):
            cleaned_rows.append(row)

    return cleaned_rows

def median(values):
    present_values = [
        value for value in values
        if value is not None
    ]
    if not present_values:
        return None
    return statistics.median(present_values)

def fmt(value):
    if value is None or value == '':
        return '--'
    if isinstance(value, float):
        return f'{value:.3g}'
    return str(value)

def table(name, headers, rows, caption, output=ROOT / 'outputs' / 'tables'):
    output.mkdir(parents=True, exist_ok=True)

    output_rows = [
        dict(zip(headers, row))
        for row in rows
    ]
    output_path = output / (name + '.csv')
    write_csv(output_path, output_rows, headers)

def grouped(rows, key):
    grouped_rows = defaultdict(list)

    for row in rows:
        group_key = key(row)
        grouped_rows[group_key].append(row)

    return grouped_rows

def preprocess(sources, data, out, expected=None):
    import importlib

    module_name = (
        f'{__package__}.01_preprocess'
        if __package__
        else '01_preprocess'
    )
    preprocessing_module = importlib.import_module(module_name)
    return preprocessing_module.preprocess(sources, data, out, expected)