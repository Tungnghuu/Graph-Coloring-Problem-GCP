from pathlib import Path
import csv
import hashlib
import json
from collections import defaultdict

if __package__:
    from .analysis_core import (
        ATTEMPT_FIELDS,
        ENCODINGS,
        FIELDS,
        METHODS,
        PROJECT,
        ROOT,
        flag,
        grouped,
        integer,
        number,
        read_csv,
        write_csv,
    )
else:
    from analysis_core import (
        ATTEMPT_FIELDS,
        ENCODINGS,
        FIELDS,
        METHODS,
        PROJECT,
        ROOT,
        flag,
        grouped,
        integer,
        number,
        read_csv,
        write_csv,
    )


def dataset_index(data):
    graph_index = defaultdict(list)

    for path in sorted(data.rglob('*.col')):
        try:
            for line in path.read_text().splitlines():
                parts = line.split()
                if parts and parts[0] == 'p' and len(parts) >= 4:
                    graph_index[path.stem].append(
                        (
                            path.parent.name,
                            int(parts[2]),
                            int(parts[3]),
                            str(path.relative_to(data)),
                        )
                    )
                    break
        except (OSError, ValueError, UnicodeError):
            continue

    return graph_index


def identity(path,rows):
    file_name = path.stem.removesuffix('_res')
    encoding = ''
    encodings_by_length = sorted(ENCODINGS, key=len, reverse=True)

    for possible_encoding in encodings_by_length:
        if file_name.endswith('_' + possible_encoding):
            encoding = possible_encoding
            break

    if encoding:
        graph_name = file_name[:-(len(encoding) + 1)]
    else:
        graph_name = file_name

    method = ''
    if rows:
        method = METHODS.get(rows[0].get('method', ''), '')

    if not method:
        for possible_method in ('Binary', 'Repeated', 'Incremental'):
            if possible_method in path.parts:
                method = possible_method
                break

    if encoding in ('SAT', 'POP', 'POHP'):
        backend = 'PySAT-unspecified'
    else:
        backend = encoding

    return graph_name, method, encoding, backend


def measured_sum(rows,key):
    values = [row.get(key) for row in rows]
    if not values:
        return None
    if any(value is None for value in values):
        return None
    return sum(values)


def summarize(attempts, meta=None):
    if meta is None:
        meta = {}

    if attempts:
        first_attempt = attempts[0]
    else:
        first_attempt = {}

    sat_color_counts = [
        row['k']
        for row in attempts
        if row['status'] == 'SAT' and row.get('valid_coloring') is True
    ]

    timeout_color_counts = [
        row['best_k']
        for row in attempts
        if row.get('valid_coloring') is True
        and row.get('best_k') is not None
    ]
    sat_color_counts.extend(timeout_color_counts)

    if sat_color_counts:
        best_color_count = min(sat_color_counts)
    else:
        best_color_count = None

    vertex_count = first_attempt.get('vertices')

    lower_bound_candidates = [
        integer(meta.get('initial_lb')),
        integer(meta.get('final_lb')),
    ]
    lower_bound_candidates = [
        candidate
        for candidate in lower_bound_candidates
        if candidate is not None
    ]

    # UNSAT result at k -> a lower bound of at least k + 1
    for attempt in attempts:
        if attempt['status'] == 'UNSAT':
            lower_bound_candidates.append(attempt['k'] + 1)

    # A graph need atleast one color
    if vertex_count is not None:
        if vertex_count > 0:
            lower_bound_candidates.append(1)
        else:
            lower_bound_candidates.append(0)

    if lower_bound_candidates:
        lower_bound = max(lower_bound_candidates)
    else:
        lower_bound = None

    bounds_are_inconsistent = (
        best_color_count is not None
        and lower_bound is not None
        and lower_bound > best_color_count
    )

    if best_color_count is None or bounds_are_inconsistent:
        proof_status = 'unknown'
    elif lower_bound == best_color_count:
        proof_status = 'optimal'
    else:
        proof_status = 'feasible'

    timed_out = any(
        row['status'] == 'TIMEOUT' or row.get('timed_out') is True
        for row in attempts
    )
    timed_out = timed_out or meta.get('completion') == 'Timeout'

    completion = meta.get('completion')
    allowed_completions = (
        'Completed',
        'Partial',
        'Timeout',
        'Missing',
        'Error',
    )
    if completion not in allowed_completions:
        has_error = any(row['status'] == 'ERROR' for row in attempts)
        if has_error:
            completion = 'Error'
        elif timed_out:
            completion = 'Timeout'
        elif proof_status == 'optimal':
            completion = 'Completed'
        else:
            completion = 'Partial'

    bounds_times = [row.get('bounds_time') for row in attempts]
    quality_notices = []

    if bounds_are_inconsistent:
        quality_notices.append('contradictory_bounds')

    repeated_bound_time = any(
        value is not None and value > 0
        for value in bounds_times[1:]
    )
    if repeated_bound_time:
        quality_notices.append('repeated_bounds_time')

    recorded_time = measured_sum(attempts, 'total_time')
    wall_time = number(meta.get('total_wall_time'))

    if attempts:
        first_bounds_time = bounds_times[0]
    else:
        first_bounds_time = None

    if wall_time is not None:
        total_time = wall_time
        time_basis = 'wall+precomputed_bounds'
    else:
        total_time = recorded_time
        time_basis = 'recorded_components'

    if best_color_count and lower_bound is not None and not bounds_are_inconsistent:
        optimality_gap = (best_color_count - lower_bound) / best_color_count
    elif best_color_count == 0 and lower_bound == 0:
        optimality_gap = 0
    else:
        optimality_gap = None

    if attempts and all(
        row.get('solver_called') is not None for row in attempts
    ):
        solver_call_count = sum(row['solver_called'] for row in attempts)
    else:
        solver_call_count = None

    timeout_phases = sorted({
        row.get('timeout_phase', '')
        for row in attempts
        if row.get('timeout_phase')
    })

    return {
        'attempts': len(attempts),
        'solver_calls': solver_call_count,
        'best_k': best_color_count,
        'lower_bound': lower_bound,
        'gap': optimality_gap,
        'proof': proof_status,
        'timeout': timed_out,
        'completion': completion,
        'termination_reason': meta.get('termination_reason', 'not recorded'),
        'timeout_phase': ','.join(timeout_phases),
        'encoding_time': measured_sum(attempts, 'encoding_time'),
        'setup_time': measured_sum(attempts, 'setup_time'),
        'solving_time': measured_sum(attempts, 'solving_time'),
        'bounds_time': first_bounds_time,
        'recorded_time': recorded_time,
        'total_time': total_time,
        'time_basis': time_basis,
        'num_variables': first_attempt.get('num_variables'),
        'num_clauses': first_attempt.get('num_clauses'),
        'first_k': first_attempt.get('k'),
        'quality': ';'.join(quality_notices),
    }


def preprocess(sources, data, out, expected=None):
    output_directory = out
    graph_index = dataset_index(data)

    runs = []
    attempts = []
    issues = []
    sweeps = []
    configurations = []
    inventory = []

    result_paths = set()
    for source_directory in sources:
        if not source_directory.exists():
            continue
        for result_path in source_directory.rglob('*.csv'):
            result_paths.add(result_path.resolve())

    sorted_result_paths = sorted(result_paths)

    for result_path in sorted_result_paths:
        source_name = str(result_path)

        try:
            file_rows = read_csv(result_path)
        except (OSError, UnicodeError, csv.Error) as error:
            issues.append({
                'source': source_name,
                'issue': 'unreadable',
                'detail': str(error),
            })
            file_rows = []

        is_k_sweep = result_path.stem.endswith('_k_sweep')
        graph_name, method, encoding, backend = identity(
            result_path,
            file_rows,
        )

        if is_k_sweep:
            if file_rows:
                recorded_graph = file_rows[0].get('graph')
                if recorded_graph:
                    graph_name = Path(recorded_graph).stem
                else:
                    graph_name = result_path.stem.removesuffix(
                        '_POHP_k_sweep'
                    )
            else:
                graph_name = result_path.stem.removesuffix(
                    '_POHP_k_sweep'
                )

            method = 'K-sweep'
            encoding = 'POHP'
            backend = 'PySAT-unspecified'

        graph_matches = graph_index.get(graph_name, [])
        same_folder_matches = [
            match
            for match in graph_matches
            if match[0] == result_path.parent.name
        ]
        if len(same_folder_matches) == 1:
            graph_matches = same_folder_matches

        if len(graph_matches) == 1:
            graph_group, vertex_count, edge_count, graph_id = graph_matches[0]
        else:
            graph_group = ''
            vertex_count = None
            edge_count = None
            graph_id = graph_name

        metadata = {}
        metadata_path = result_path.with_suffix('.meta.json')
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text())
            except (ValueError, OSError) as error:
                issues.append({
                    'source': source_name,
                    'issue': 'invalid_manifest',
                    'detail': str(error),
                })

        backend = metadata.get('solver', backend)

        required_metadata_fields = (
            'config_id',
            'environment',
            'implementation',
            'time_limit',
            'encoding_time_limit',
            'total_time_limit',
        )
        metadata_is_verified = (
            metadata.get('schema_version') == 2
            and all(
                field in metadata
                for field in required_metadata_fields
            )
        )

        comparison_fields = (
            'environment',
            'implementation',
            'time_limit',
            'encoding_time_limit',
            'total_time_limit',
            'symmetry_breaking',
            'parameters',
            'initial_lb',
            'initial_ub',
        )
        comparison_metadata = {
            field: metadata.get(field)
            for field in comparison_fields
        }

        if metadata_is_verified:
            comparison_json = json.dumps(
                comparison_metadata,
                sort_keys=True,
            )
            comparison_id = hashlib.sha256(
                comparison_json.encode()
            ).hexdigest()[:16]
        else:
            comparison_id = 'unverified'

        base_record = {
            'source': source_name,
            'run_id': metadata.get('run_id', source_name),
            'graph': graph_name,
            'graph_id': graph_id,
            'group': graph_group,
            'vertices': vertex_count,
            'edges': edge_count,
            'method': method,
            'encoding': encoding,
            'backend': backend,
            'config_id': metadata.get('config_id', 'unverified'),
            'comparison_config': comparison_id,
            'metadata_verified': metadata_is_verified,
        }

        if is_k_sweep:
            schema_name = 'k_sweep'
        elif metadata:
            schema_name = 'v2'
        else:
            schema_name = 'legacy'

        inventory.append({
            'source': source_name,
            'schema': schema_name,
            'rows': len(file_rows),
            'graph_id': graph_id,
        })
        configurations.append({
            'source': source_name,
            'verified': metadata_is_verified,
            'metadata': json.dumps(metadata, sort_keys=True),
        })

        if len(graph_matches) != 1:
            issues.append({
                'source': source_name,
                'issue': 'graph_unresolved',
                'detail': graph_name,
            })

        parsed_attempts = []
        for line_number, row in enumerate(file_rows, start=2):
            color_count = integer(row.get('k'))
            status = str(row.get('status', '')).upper()
            allowed_statuses = (
                'SAT',
                'UNSAT',
                'TIMEOUT',
                'UNKNOWN',
                'ERROR',
            )

            if (
                color_count is None
                or color_count < 0
                or status not in allowed_statuses
            ):
                issues.append({
                    'source': source_name,
                    'issue': 'invalid_row',
                    'detail': f'line {line_number}: k/status',
                })
                continue

            attempt = dict(
                base_record,
                k=color_count,
                status=status,
                valid_coloring=flag(row.get('valid_coloring')),
                solver_called=flag(row.get('solver_called')),
                timed_out=flag(row.get('timed_out')),
                timeout_phase=row.get('timeout_phase', ''),
                backend_status=row.get('backend_status', ''),
            )

            # The file path and the row should agree about method and encoding.
            if not is_k_sweep:
                row_method = METHODS.get(row.get('method', ''), '')
                row_encoding_name = row.get('encoding', '').removesuffix(
                    'Encoding'
                )
                encoding_aliases = {
                    'GurobiILP': 'Gurobi_ILP',
                    'CPLEXMIP': 'CPLEX_MIP',
                    'CPLEXCP': 'CPLEX_CP',
                }
                row_encoding = encoding_aliases.get(
                    row_encoding_name,
                    row_encoding_name,
                )

                method_does_not_match = (
                    row_method and row_method != method
                )
                encoding_does_not_match = (
                    row_encoding and row_encoding != encoding
                )
                if method_does_not_match or encoding_does_not_match:
                    issues.append({
                        'source': source_name,
                        'issue': 'identity_mismatch',
                        'detail': f'line {line_number}',
                    })
                    continue

            numeric_fields = (
                'num_variables',
                'num_clauses',
                'bounds_time',
                'encoding_time',
                'setup_time',
                'solving_time',
                'total_time',
                'best_k',
            )
            for field in numeric_fields:
                attempt[field] = number(row.get(field))
                if attempt[field] is not None and attempt[field] < 0:
                    attempt[field] = None
                    issues.append({
                        'source': source_name,
                        'issue': 'negative_value',
                        'detail': f'line {line_number}: {field}',
                    })

            if (
                status == 'SAT'
                and attempt['valid_coloring'] is False
            ):
                issues.append({
                    'source': source_name,
                    'issue': 'invalid_coloring',
                    'detail': f'line {line_number}: SAT with invalid coloring',
                })

            parsed_attempts.append(attempt)

        # K-sweep files contain independent attempts, not full run summaries.
        if is_k_sweep:
            sweeps.extend(parsed_attempts)
            if not parsed_attempts:
                issues.append({
                    'source': source_name,
                    'issue': 'missing_sweep',
                    'detail': 'No completed result',
                })
            continue

        run_summary = summarize(parsed_attempts, metadata)

        if not file_rows:
            file_was_unreadable = any(
                issue['source'] == source_name
                and issue['issue'] == 'unreadable'
                for issue in issues
            )
            if (
                metadata.get('completion') == 'Error'
                or file_was_unreadable
            ):
                run_summary['completion'] = 'Error'
            else:
                run_summary['completion'] = 'Missing'

            issues.append({
                'source': source_name,
                'issue': 'empty',
                'detail': 'No completed attempt; see manifest for errors',
            })
        elif not parsed_attempts:
            run_summary['completion'] = 'Error'

        if len(parsed_attempts) != len(file_rows):
            run_summary['quality'] += ';invalid_rows'

        if len(graph_matches) != 1:
            run_summary['quality'] += ';graph_unresolved'

        has_identity_problem = any(
            issue['source'] == source_name
            and issue['issue'] == 'identity_mismatch'
            for issue in issues
        )
        if has_identity_problem:
            run_summary['quality'] += ';identity_mismatch'

        has_invalid_coloring = any(
            issue['source'] == source_name
            and issue['issue'] == 'invalid_coloring'
            for issue in issues
        )
        if has_invalid_coloring:
            run_summary['quality'] += ';invalid_coloring'

        runs.append(dict(base_record, **run_summary))
        attempts.extend(parsed_attempts)

    configuration_groups = grouped(
        runs,
        lambda row: (
            row['graph_id'],
            row['method'],
            row['encoding'],
            row['backend'],
            row['config_id'],
        ),
    )
    for group_key, matching_runs in configuration_groups.items():
        if len(matching_runs) <= 1:
            continue

        for run in matching_runs:
            run['quality'] += ';repeated_configuration'
            issues.append({
                'source': run['source'],
                'issue': 'repeated_configuration',
                'detail': str(group_key),
            })

    if expected:
        expected_rows = read_csv(expected)
        for expected_row in expected_rows:
            already_present = False

            for run in runs:
                fields_match = all(
                    str(run.get(field, '')) == str(value)
                    for field, value in expected_row.items()
                    if value and field in FIELDS
                )
                if fields_match:
                    already_present = True
                    break

            if already_present:
                continue

            missing_run = {
                field: None
                for field in FIELDS
            }
            missing_run.update(
                expected_row,
                source='',
                completion='Missing',
                proof='unknown',
                timeout=False,
                metadata_verified=False,
                quality='',
                attempts=0,
            )
            runs.append(missing_run)

    write_csv(output_directory / 'summary_runs.csv', runs, FIELDS)
    write_csv(
        output_directory / 'attempts.csv',
        attempts,
        ATTEMPT_FIELDS,
    )
    write_csv(
        output_directory / 'k_sweep.csv',
        sweeps,
        ATTEMPT_FIELDS,
    )
    write_csv(
        output_directory / 'data_quality.csv',
        issues,
        ['source', 'issue', 'detail'],
    )
    write_csv(
        output_directory / 'inventory.csv',
        inventory,
        ['source', 'schema', 'rows', 'graph_id'],
    )
    write_csv(
        output_directory / 'configurations.csv',
        configurations,
        ['source', 'verified', 'metadata'],
    )

    coverage_groups = grouped(
        runs,
        lambda row: (
            row.get('method') or '',
            row.get('encoding') or '',
            row.get('group') or '',
        ),
    )
    coverage = []
    completion_states = (
        'Completed',
        'Partial',
        'Timeout',
        'Missing',
        'Error',
    )
    for group_key, matching_runs in sorted(coverage_groups.items()):
        group_values = dict(
            zip(('method', 'encoding', 'group'), group_key)
        )
        for completion_state in completion_states:
            group_values[completion_state] = sum(
                run['completion'] == completion_state
                for run in matching_runs
            )
        coverage.append(group_values)

    write_csv(
        output_directory / 'coverage.csv',
        coverage,
        [
            'method',
            'encoding',
            'group',
            'Completed',
            'Partial',
            'Timeout',
            'Missing',
            'Error',
        ],
    )

    reruns = []
    for run in runs:
        reasons = []

        if not run['metadata_verified']:
            reasons.append(
                'unverified historical configuration/timing/bounds'
            )
        if run['encoding'] == 'POP' and not run['metadata_verified']:
            reasons.append(
                'legacy POP implementation not certified as partial order'
            )
        if run['completion'] in ('Missing', 'Error', 'Partial'):
            reasons.append(run['completion'])
        if run['quality']:
            reasons.append(run['quality'])

        if reasons:
            reruns.append({
                'source': run['source'],
                'graph_id': run['graph_id'],
                'method': run['method'],
                'encoding': run['encoding'],
                'reason': '; '.join(reasons),
            })

    write_csv(
        output_directory / 'rerun_needed.csv',
        reruns,
        ['source', 'graph_id', 'method', 'encoding', 'reason'],
    )

    return runs, attempts, issues


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Normalize experiment CSV files.'
    )
    parser.add_argument(
        '--source',
        type=Path,
        action='append',
        help='Input directory; repeat for multiple sources.',
    )
    parser.add_argument(
        '--data',
        type=Path,
        default=PROJECT / 'data',
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=ROOT / 'processed',
    )
    parser.add_argument('--expected', type=Path)
    args = parser.parse_args()

    input_sources = args.source or [PROJECT / 'results', ROOT / 'raw_results']
    runs, attempts, issues = preprocess(
        input_sources, args.data, args.output, args.expected
    )
    print(
        f'Preprocessed {len(runs)} runs, {len(attempts)} attempts; '
        f'{len(issues)} quality notices'
    )


if __name__ == '__main__':
    main()
