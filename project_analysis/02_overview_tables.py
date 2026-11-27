if __package__:
    from .reports_common import (
        ROOT, emit, graph_group_sort_key, grouped, read_csv,
    )
else:
    from reports_common import (
        ROOT, emit, graph_group_sort_key, grouped, read_csv,
    )

if __package__:
    from .analysis_core import load_runs
else:
    from analysis_core import load_runs

def overview(runs, issues):
    coverage_path = ROOT / 'processed' / 'coverage.csv'
    coverage_rows = read_csv(coverage_path)
    coverage_headers = [
        'method', 'encoding', 'group', 'Completed', 'Partial',
        'Timeout', 'Missing', 'Error',
    ]
    coverage_table_rows = []
    for row in coverage_rows:
        coverage_table_rows.append([
            row[header]
            for header in coverage_headers
        ])
    emit(
        'coverage',
        coverage_headers,
        coverage_table_rows,
        'File/run inventory; Missing includes explicit expected manifest only. '
        'Timeout is independent of feasible/optimal.',
    )
    issues_by_type = grouped(
        issues,
        lambda row: row['issue'],
    )
    quality_rows = []
    for issue_name, matching_issues in sorted(issues_by_type.items()):
        source_count = len({
            row['source']
            for row in matching_issues
        })
        quality_rows.append([
            issue_name,
            len(matching_issues),
            source_count,
        ])
    emit(
        'data_quality',
        ['Issue', 'Occurrences', 'Files'],
        quality_rows,
        'Quality notices; categories may overlap.',
    )
    configurations_path = ROOT / 'processed' / 'configurations.csv'
    configurations = read_csv(configurations_path)
    configuration_coverage = []
    for verified_value in ('True', 'False'):
        file_count = sum(
            row['verified'] == verified_value
            for row in configurations
        )
        configuration_coverage.append([verified_value, file_count])
    emit(
        'configuration_coverage',
        ['Verified', 'Files'],
        configuration_coverage,
        'Full environment and parameters are in processed/configurations.csv; '
        'never inferred from this machine for old runs.',
    )
    graph_records = {}
    for row in runs:
        if row['vertices'] is not None:
            graph_records[row['graph_id']] = row

    graphs_by_group = grouped(
        list(graph_records.values()),
        lambda row: row['group'],
    )
    dataset_rows = []
    for group_name, group_rows in sorted(
        graphs_by_group.items(),
        key=lambda item: graph_group_sort_key(item[0]),
    ):
        dataset_rows.append([
            group_name,
            len(group_rows),
            min(row['vertices'] for row in group_rows),
            max(row['vertices'] for row in group_rows),
            min(row['edges'] for row in group_rows),
            max(row['edges'] for row in group_rows),
        ])
    emit(
        'dataset_overview',
        [
            'Bucket',
            'Graphs',
            'Vertices min',
            'Vertices max',
            'Edges min',
            'Edges max',
        ],
        dataset_rows,
        'Distinct graph identities represented by input files; '
        'includes missing/error runs.',
    )
    import json

    metadata_rows = []
    for row in configurations:
        metadata = json.loads(row['metadata'])
        environment = metadata.get('environment', {})
        metadata_rows.append([
            row['source'],
            metadata.get('solver'),
            metadata.get('started_at'),
            environment.get('cpu'),
            environment.get('ram_bytes'),
            environment.get('os'),
            environment.get('python'),
            str(environment.get('versions', {})),
            metadata.get('parameters'),
            metadata.get('time_limit'),
            metadata.get('encoding_time_limit'),
            metadata.get('total_time_limit'),
        ])
    emit(
        'configurations',
        [
            'Source', 'Solver', 'Date UTC', 'CPU', 'RAM bytes', 'OS',
            'Python', 'Versions', 'Parameters', 'Solve limit',
            'Encoding limit', 'Run limit',
        ],
        metadata_rows,
        'Blank means not recorded. Run limit excludes externally '
        'precomputed bounds; wall time includes their measured cost.',
    )

def main():
    runs = load_runs()
    issues = read_csv(ROOT / 'processed' / 'data_quality.csv')
    overview(runs, issues)
    print('Overview tables written')

if __name__ == '__main__':
    main()