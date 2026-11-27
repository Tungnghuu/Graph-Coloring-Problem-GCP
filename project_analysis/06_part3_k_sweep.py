if __package__:
    from .reports_common import (
        ROOT,
        emit,
        graph_id_sort_key,
        grouped,
        median,
        no_data,
        number,
        plt,
        read_csv,
        save,
    )
else:
    from reports_common import (
        ROOT,
        emit,
        graph_id_sort_key,
        grouped,
        median,
        no_data,
        number,
        plt,
        read_csv,
        save,
    )

def part3():
    sweep_path = ROOT / 'processed' / 'k_sweep.csv'
    sweep_rows = read_csv(sweep_path)

    numeric_fields = (
        'k',
        'total_time',
        'solving_time',
        'encoding_time',
    )
    for row in sweep_rows:
        for field in numeric_fields:
            row[field] = number(row[field])

    inventory_path = ROOT / 'processed' / 'inventory.csv'
    inventory_rows = read_csv(inventory_path)
    coverage_rows = []
    for row in inventory_rows:
        if row['schema'] != 'k_sweep':
            continue

        if int(row['rows']) == 0:
            status = 'Missing'
        else:
            status = 'Recorded attempts; completion may be unknown'

        coverage_rows.append([
            row['source'],
            row['graph_id'],
            row['rows'],
            status,
        ])

    emit(
        'p3_coverage',
        ['Source', 'Graph', 'Rows', 'Status'],
        coverage_rows,
        'Header-only sweep is Missing, not Timeout.',
    )

    rows_by_graph = grouped(
        sweep_rows,
        lambda row: row['graph_id'],
    )
    summary_rows = []

    for graph_id, graph_rows in sorted(
        rows_by_graph.items(),
        key=lambda item: graph_id_sort_key(item[0]),
    ):
        graph_rows = sorted(
            graph_rows,
            key=lambda row: row['k'],
        )
        plt.figure(figsize=(9, 5))

        timing_lines = (
            ('encoding_time', 'Encoding time'),
            ('solving_time', 'Solving time'),
            ('total_time', 'Total runtime'),
        )
        for field, line_label in timing_lines:
            measured_rows = [
                row for row in graph_rows
                if row[field] is not None
            ]
            if not measured_rows:
                continue

            plt.plot(
                [row['k'] for row in measured_rows],
                [row[field] for row in measured_rows],
                alpha=0.7,
                label=line_label,
            )

        rows_with_total_time = [
            row for row in graph_rows
            if row['total_time'] is not None
        ]
        status_markers = (
            ('SAT', 'o'),
            ('UNSAT', 's'),
            ('TIMEOUT', 'x'),
            ('UNKNOWN', '^'),
        )
        for status, marker in status_markers:
            status_rows = [
                row for row in rows_with_total_time
                if row['status'] == status
            ]
            plt.scatter(
                [row['k'] for row in status_rows],
                [row['total_time'] for row in status_rows],
                marker=marker,
                label=status,
            )

        plt.yscale('symlog', linthresh=0.001)
        plt.xlabel('k')
        plt.ylabel('Runtime per k (s)')
        plt.title(
            graph_id
            + '; independent solves, historical configuration may be unknown'
        )
        plt.legend()

        figure_name = (
            'p3_'
            + graph_id.replace('/', '_').replace('.col', '')
        )
        save(figure_name)

        for status, marker in status_markers:
            status_rows = [
                row for row in rows_with_total_time
                if row['status'] == status
            ]
            if not status_rows:
                continue

            peak_row = max(
                status_rows,
                key=lambda row: row['total_time'],
            )
            total_times = [
                row['total_time']
                for row in status_rows
            ]
            color_counts = [
                row['k']
                for row in status_rows
            ]
            summary_rows.append([
                graph_id,
                status,
                len(status_rows),
                min(color_counts),
                max(color_counts),
                median(total_times),
                peak_row['k'],
                peak_row['total_time'],
            ])

    if not rows_by_graph:
        no_data('Runtime by k')
    else:
        plt.figure(figsize=(10, 6))
        for graph_id, graph_rows in sorted(
            rows_by_graph.items(),
            key=lambda item: graph_id_sort_key(item[0]),
        ):
            total_time_rows = [
                row for row in graph_rows
                if row['total_time'] is not None
            ]
            total_time_rows = sorted(
                total_time_rows,
                key=lambda row: row['k'],
            )

            plt.plot(
                [row['k'] for row in total_time_rows],
                [row['total_time'] for row in total_time_rows],
                label=graph_id,
            )

        plt.xlabel('k')
        plt.ylabel('Runtime per k (s)')
        plt.yscale('symlog', linthresh=0.001)
        plt.legend(fontsize=7)
        plt.title(
            'Total runtime only; exploratory k sweep; one graph per bucket '
            'is not a population conclusion'
        )

    save('p3_runtime_k')

    summary_headers = [
        'Graph',
        'Status',
        'Attempts',
        'Min k',
        'Max k',
        'Median runtime',
        'Peak k',
        'Peak runtime',
    ]
    emit(
        'p3_summary',
        summary_headers,
        summary_rows,
        'Per-k observed runtime, not total Repeated search time. '
        'Timeout values are censored.',
    )

def main():
    part3()

if __name__ == '__main__':
    main()