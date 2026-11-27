if __package__:
    from .reports_common import (
        SAT,
        best_observed_sources,
        boxes,
        emit,
        grouped,
        heat,
        iqr,
        median,
        paired,
        plt,
        save,
        select,
    )
else:
    from reports_common import (
        SAT,
        best_observed_sources,
        boxes,
        emit,
        grouped,
        heat,
        iqr,
        median,
        paired,
        plt,
        save,
        select,
    )

if __package__:
    from .analysis_core import load_runs
else:
    from analysis_core import load_runs

def part2a(runs, exploratory=False):
    methods = ('Incremental', 'Repeated', 'Binary')
    for encoding in SAT:
        tag = 'p2a_' + encoding
        if exploratory:
            tag += '_exploratory'

        rows = select(
            runs,
            'method',
            methods,
            'p2a',
            tag,
            lambda row: row['encoding'] == encoding,
            exploratory=exploratory,
        )
        best_sources = best_observed_sources(rows, 'p2a')

        def is_included_for_runtime(row):
            encoding_matches = row['encoding'] == encoding
            is_proven = row['proof'] == 'optimal'
            is_best_observed = row['source'] in best_sources
            return (
                encoding_matches
                and (is_proven or is_best_observed)
            )

        speed_rows = select(
            runs,
            'method',
            methods,
            'p2a',
            tag + '_runtime',
            is_included_for_runtime,
            metric='total_time',
            exploratory=exploratory,
        )

        if exploratory:
            title = 'EXPLORATORY; ' + encoding
        else:
            title = 'Verified; ' + encoding

        boxes(
            speed_rows,
            lambda row: row['group'] + ' / ' + row['method'],
            'total_time',
            title + '; common proven-optimal or best-observed runs; k may differ',
            tag + '_total_time',
        )
        heat(rows, 'method', title, tag + '_timeout')

        paired(
            rows,
            'method',
            methods,
            'best_k',
            tag + '_best_colors',
            title,
            'p2a',
        )

        for metric in ('attempts',):
            plt.figure(figsize=(8, 5))

            for method in methods:
                method_rows = [
                    row for row in rows
                    if row['method'] == method
                    and row.get(metric) is not None
                    and row['total_time'] is not None
                ]

                for did_timeout, marker in ((False, 'o'), (True, 'x')):
                    matching_rows = [
                        row for row in method_rows
                        if row['timeout'] == did_timeout
                    ]
                    if did_timeout:
                        legend_label = method + ' timeout'
                    else:
                        legend_label = method

                    plt.scatter(
                        [row[metric] for row in matching_rows],
                        [row['total_time'] for row in matching_rows],
                        marker=marker,
                        label=legend_label,
                        alpha=0.6,
                    )

            plt.yscale('symlog', linthresh=1)
            plt.xlabel(metric)
            plt.ylabel(
                'Observed runtime (s), not time to solution for timeout'
            )
            plt.title(title)
            plt.legend(fontsize=7)
            save(tag + '_' + metric + '_time')

        method_summary_rows = []
        rows_by_method = grouped(rows, lambda row: row['method'])
        for method, method_rows in sorted(rows_by_method.items()):
            method_speed_rows = [
                row for row in speed_rows
                if row['method'] == method
            ]
            runtimes = [
                row['total_time']
                for row in method_speed_rows
            ]
            attempts = [
                row['attempts']
                for row in method_rows
            ]
            solver_calls = [
                row['solver_calls']
                for row in method_rows
            ]
            color_counts = [
                row['best_k']
                for row in method_rows
            ]
            optimal_count = sum(
                row['proof'] == 'optimal'
                for row in method_rows
            )
            optimal_percentage = 100 * optimal_count / len(method_rows)
            timeout_count = sum(
                row['timeout']
                for row in method_rows
            )

            method_summary_rows.append([
                method,
                len(method_rows),
                len(method_speed_rows),
                median(runtimes),
                iqr(runtimes),
                timeout_count,
                median(attempts),
                median(solver_calls),
                median(color_counts),
                optimal_percentage,
            ])

        method_headers = [
            'Method',
            'Runs',
            'Optimal/best-observed timed n',
            'Median time',
            'IQR time',
            'Timeout',
            'Median attempts',
            'Median calls',
            'Median best colors',
            'Optimal %',
        ]
        emit(
            tag + '_methods',
            method_headers,
            method_summary_rows,
            title
            + '; runtime includes common proven or best-observed runs, '
            + 'where k may differ; median colors describes this dataset, '
            + 'not paired quality advantage.',
        )

        result_rows = []
        for row in rows:
            result_rows.append([
                row['graph_id'],
                row['method'],
                row['best_k'],
                row['lower_bound'],
                row['proof'],
                row['timeout'],
            ])
        emit(
            tag + '_results',
            ['Graph', 'Method', 'UB', 'LB', 'Proof', 'Timeout'],
            result_rows,
            title,
        )

def main():
    part2a(load_runs())
    print('Search method reports written')

if __name__ == '__main__':
    main()