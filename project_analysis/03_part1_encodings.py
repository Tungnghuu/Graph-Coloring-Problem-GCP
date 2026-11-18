if __package__:
    from .reports_common import (
        SAT,
        best_observed_sources,
        boxes,
        common,
        emit,
        grouped,
        heat,
        iqr,
        median,
        paired,
        plt,
        save,
        select,
        stratum,
    )
else:
    from reports_common import (
        SAT,
        best_observed_sources,
        boxes,
        common,
        emit,
        grouped,
        heat,
        iqr,
        median,
        paired,
        plt,
        save,
        select,
        stratum,
    )

if __package__:
    from .analysis_core import load_runs
else:
    from analysis_core import load_runs

def part1(runs, method='Repeated', exploratory=False):
    tag = 'p1_' + method
    if exploratory:
        tag += '_exploratory'

    rows = select(
        runs,
        'encoding',
        SAT,
        'p1',
        tag,
        lambda row: row['method'] == method,
        exploratory=exploratory,
    )
    best_sources = best_observed_sources(rows, 'p1')

    if exploratory:
        title = 'EXPLORATORY historical logs'
    else:
        title = 'Verified matched runs'

    for metric in ('encoding_time', 'solving_time'):
        def is_included_for_timing(row):
            is_requested_method = row['method'] == method
            is_proven = row['proof'] == 'optimal'
            is_best_observed = row['source'] in best_sources
            return (
                is_requested_method
                and (is_proven or is_best_observed)
            )

        timing_rows = select(
            runs,
            'encoding',
            SAT,
            'p1',
            tag + '_' + metric,
            is_included_for_timing,
            metric,
            exploratory,
        )
        timing_title = (
            title
            + '; optimal or best-observed runs; '
            + method
        )
        boxes(
            timing_rows,
            lambda row: row['group'] + ' / ' + row['encoding'],
            metric,
            timing_title,
            tag + '_' + metric,
        )
    heat(
        rows,
        'encoding',
        title + '; ' + method,
        tag + '_timeout',
    )
    timeout_phase_rows = []
    for encoding in SAT:
        for phase in ('encoding', 'solving', 'total'):
            phase_count = 0
            for row in rows:
                recorded_phases = (
                    row.get('timeout_phase') or ''
                ).split(',')
                if row['encoding'] == encoding and phase in recorded_phases:
                    phase_count += 1
            timeout_phase_rows.append([
                encoding,
                phase,
                phase_count,
            ])
    emit(
        tag + '_timeout_phases',
        ['Encoding', 'Phase', 'Runs'],
        timeout_phase_rows,
        'Recorded timeout phase only; historical unknown phases are not inferred.',
    )
    size_rows = select(
        runs,
        'encoding',
        SAT,
        'p1',
        tag + '_sizes',
        lambda row: row['method'] == method,
        exploratory=exploratory,
        extra='first_k',
    )

    for metric in ('num_variables', 'num_clauses'):
        measured_size_rows = [
            row for row in size_rows
            if row.get(metric) is not None
        ]
        matched_size_rows = common(
            measured_size_rows,
            'encoding',
            SAT,
            lambda row: (stratum(row, 'p1'), row['first_k']),
        )

        plt.figure(figsize=(9, 5))
        for encoding in SAT:
            encoding_rows = [
                row for row in matched_size_rows
                if row['encoding'] == encoding
                and row.get(metric) is not None
            ]
            rows_by_vertex_count = grouped(
                encoding_rows,
                lambda row: row['vertices'],
            )
            vertex_counts = sorted(rows_by_vertex_count)
            median_sizes = []
            for vertex_count in vertex_counts:
                values = [
                    row[metric]
                    for row in rows_by_vertex_count[vertex_count]
                ]
                median_sizes.append(median(values))

            plt.plot(
                vertex_counts,
                median_sizes,
                marker='o',
                label=encoding,
            )

        plt.xlabel('Vertices')
        plt.ylabel(metric)
        plt.title(
            title
            + '; first attempt, matched graph and k; median at each n'
        )
        plt.legend()
        save(tag + '_' + metric)

    def is_included_for_total_runtime(row):
        is_requested_method = row['method'] == method
        is_proven = row['proof'] == 'optimal'
        is_best_observed = row['source'] in best_sources
        return (
            is_requested_method
            and (is_proven or is_best_observed)
        )

    speed_rows = select(
        runs,
        'encoding',
        SAT,
        'p1',
        tag + '_runtime',
        is_included_for_total_runtime,
        metric='total_time',
        exploratory=exploratory,
    )
    paired(
        speed_rows,
        'encoding',
        SAT,
        'total_time',
        tag + '_paired_time',
        title + '; optimal or best-observed runs; k may differ',
        'p1',
    )

    summary_headers = [
        'Encoding',
        'Graphs',
        'Runs',
        'Optimal/best-observed timed n',
        'Encoding timed n',
        'Solve timed n',
        'Encoding median',
        'Encoding IQR',
        'Solve median',
        'Solve IQR',
        'Total median',
        'Total IQR',
        'Timeout',
        'Feasible',
    ]
    summary_rows = []
    rows_by_encoding = grouped(rows, lambda row: row['encoding'])

    for encoding, encoding_rows in sorted(rows_by_encoding.items()):
        completed_timing_rows = [
            row for row in speed_rows
            if row['encoding'] == encoding
        ]
        metric_samples = {}

        for metric in ('encoding_time', 'solving_time', 'total_time'):
            measured_rows = [
                row for row in speed_rows
                if row.get(metric) is not None
            ]
            common_rows = common(
                measured_rows,
                'encoding',
                SAT,
                lambda row: stratum(row, 'p1'),
            )
            metric_samples[metric] = [
                row for row in common_rows
                if row['encoding'] == encoding
            ]

        metric_summaries = []
        for metric in ('encoding_time', 'solving_time', 'total_time'):
            values = [
                row[metric]
                for row in metric_samples[metric]
            ]
            metric_summaries.extend([
                median(values),
                iqr(values),
            ])

        graph_count = len({
            row['graph_id']
            for row in encoding_rows
        })
        timeout_count = sum(
            row['timeout']
            for row in encoding_rows
        )
        feasible_count = sum(
            row['best_k'] is not None
            for row in encoding_rows
        )

        summary_rows.append([
            encoding,
            graph_count,
            len(encoding_rows),
            len(completed_timing_rows),
            len(metric_samples['encoding_time']),
            len(metric_samples['solving_time']),
            *metric_summaries,
            timeout_count,
            feasible_count,
        ])

    emit(
        tag + '_summary',
        summary_headers,
        summary_rows,
        title
        + '; runtime statistics use common proven or best-observed runs; '
        + 'k may differ; historical solve includes setup.',
    )

    result_rows = []
    for row in rows:
        result_rows.append([
            row['graph_id'],
            row['encoding'],
            row['best_k'],
            row['lower_bound'],
            row['proof'],
            row['timeout'],
            row['time_basis'],
        ])
    emit(
        tag + '_results',
        ['Graph', 'Encoding', 'UB', 'LB', 'Proof', 'Timeout', 'Time basis'],
        result_rows,
        title,
    )

    formula_size_summary = []
    sizes_by_encoding = grouped(
        size_rows,
        lambda row: row['encoding'],
    )
    for encoding in sorted(sizes_by_encoding):
        for metric in ('num_variables', 'num_clauses'):
            measured_size_rows = [
                row for row in size_rows
                if row.get(metric) is not None
            ]
            comparable_rows = common(
                measured_size_rows,
                'encoding',
                SAT,
                lambda row: (stratum(row, 'p1'), row['first_k']),
            )
            values = [
                row[metric]
                for row in comparable_rows
                if row['encoding'] == encoding
            ]
            if values:
                formula_size_summary.append([
                    encoding,
                    metric,
                    len(values),
                    median(values),
                    min(values),
                    max(values),
                ])

    emit(
        tag + '_formula_sizes',
        ['Encoding', 'Metric', 'N', 'Median', 'Min', 'Max'],
        formula_size_summary,
        'Matched graph/method/first k. Formula size depends on both graph and k.',
    )

def main():
    part1(load_runs())
    print('Encoding reports written')

if __name__ == '__main__':
    main()