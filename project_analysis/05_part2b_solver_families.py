if __package__:
    from .reports_common import (
        BACKENDS,
        P2B_ENCODINGS,
        P2B_METHODS,
        best_observed_sources,
        boxes,
        combinations,
        common,
        comparative_outcome,
        emit,
        grouped,
        heat,
        iqr,
        median,
        no_data,
        performance_profile,
        plt,
        save,
        select,
        stratum,
    )
else:
    from reports_common import (
        BACKENDS,
        P2B_ENCODINGS,
        P2B_METHODS,
        best_observed_sources,
        boxes,
        combinations,
        common,
        comparative_outcome,
        emit,
        grouped,
        heat,
        iqr,
        median,
        no_data,
        performance_profile,
        plt,
        save,
        select,
        stratum,
    )

if __package__:
    from .analysis_core import load_runs
else:
    from analysis_core import load_runs

def part2b(runs, exploratory=False):
    for method in P2B_METHODS:
        if method == 'Incremental':
            categories = P2B_ENCODINGS
            keep_unmatched_graphs = True
        else:
            categories = BACKENDS
            keep_unmatched_graphs = False

        tag = 'p2b_' + method
        if exploratory:
            tag += '_exploratory'

        rows = select(
            runs,
            'encoding',
            categories,
            'p2b',
            tag,
            lambda row: row['method'] == method,
            exploratory=exploratory,
            require_common=not keep_unmatched_graphs,
        )
        best_sources = best_observed_sources(rows)

        def is_included_for_runtime(row):
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
            categories,
            'p2b',
            tag + '_runtime',
            is_included_for_runtime,
            metric='total_time',
            exploratory=exploratory,
            require_common=not keep_unmatched_graphs,
        )

        if exploratory:
            title = 'EXPLORATORY; ' + method
        else:
            title = 'Verified; ' + method
        title += '; SAT, POP and POHP encodings'

        boxes(
            speed_rows,
            lambda row: row['encoding'],
            'total_time',
            title + '; common proven-optimal or best-observed runs; k may differ',
            tag + '_total_time',
        )
        heat(rows, 'encoding', title, tag + '_timeout')

        rows_by_encoding = grouped(
            rows,
            lambda row: row['encoding'],
        )

        if not rows:
            no_data(title)
        else:
            plt.figure(figsize=(9, 5))
            stack_bottoms = [0] * len(categories)
            outcome_colors = {
                'optimal': 'tab:blue',
                'best_observed': 'tab:green',
                'feasible': 'tab:orange',
                'unknown': 'tab:red',
            }

            for outcome in (
                'optimal',
                'best_observed',
                'feasible',
                'unknown',
            ):
                outcome_percentages = []
                for encoding in categories:
                    encoding_rows = rows_by_encoding[encoding]
                    outcome_count = sum(
                        comparative_outcome(row, best_sources) == outcome
                        for row in encoding_rows
                    )
                    percentage = 100 * outcome_count / len(encoding_rows)
                    outcome_percentages.append(percentage)

                plt.bar(
                    categories,
                    outcome_percentages,
                    bottom=stack_bottoms,
                    label=outcome,
                    color=outcome_colors[outcome],
                )
                stack_bottoms = [
                    previous + current
                    for previous, current in zip(
                        stack_bottoms,
                        outcome_percentages,
                    )
                ]

            plt.ylabel('Runs (%)')
            plt.legend()
            plt.title(title)
        save(tag + '_outcomes')

        profile = performance_profile(
            speed_rows,
            categories,
            best_sources,
        )
        if not profile:
            no_data(title + '; no proven timed runs')
        else:
            plt.figure(figsize=(8, 5))
            for encoding, points in profile.items():
                x_values = [point[0] for point in points]
                y_values = [point[1] for point in points]
                plt.step(
                    x_values,
                    y_values,
                    where='post',
                    label=encoding,
                )

            plt.xscale('log')
            plt.ylim(0, 1.02)
            plt.xlabel('Runtime / fastest proven runtime')
            plt.ylabel('Fraction of all matched cases')
            plt.legend()
            plt.title(title)
        save(tag + '_profile')

        feasible_rows = [
            row for row in rows
            if row['proof'] == 'feasible'
        ]
        boxes(
            feasible_rows,
            lambda row: row['encoding'],
            'gap',
            title + '; unproven feasible runs',
            tag + '_gap',
        )

        backend_summary_rows = []
        for encoding in categories:
            encoding_rows = rows_by_encoding.get(encoding, [])
            encoding_speed_rows = [
                row for row in speed_rows
                if row['encoding'] == encoding
            ]
            graph_count = len({
                row['graph_id']
                for row in encoding_rows
            })
            feasible_count = sum(
                row['best_k'] is not None
                for row in encoding_rows
            )
            optimal_count = sum(
                row['proof'] == 'optimal'
                for row in encoding_rows
            )
            best_observed_count = sum(
                row['source'] in best_sources
                for row in encoding_rows
            )
            timeout_count = sum(
                row['timeout']
                for row in encoding_rows
            )
            feasible_gaps = [
                row['gap']
                for row in encoding_rows
                if row['proof'] == 'feasible'
            ]
            runtimes = [
                row['total_time']
                for row in encoding_speed_rows
            ]

            backend_summary_rows.append([
                encoding,
                graph_count,
                len(encoding_rows),
                feasible_count,
                optimal_count,
                best_observed_count,
                timeout_count,
                len(encoding_speed_rows),
                median(runtimes),
                iqr(runtimes),
                median(feasible_gaps),
            ])

        if keep_unmatched_graphs:
            scope_note = (
                'Incremental includes SAT, POP and POHP only and '
                'retains available graph records.'
            )
        else:
            scope_note = (
                'Includes all six encodings and only common matched graphs.'
            )
        backend_headers = [
            'Encoding/backend',
            'Graphs',
            'Runs',
            'Feasible',
            'Optimal',
            'Best observed',
            'Timeout',
            'Optimal timed n',
            'Median time',
            'IQR time',
            'Median unproven gap',
        ]
        emit(
            tag + '_backends',
            backend_headers,
            backend_summary_rows,
            title + '; ' + scope_note
            + ' Best observed is comparative, not an optimality proof.',
        )

        result_rows = []
        for row in rows:
            result_rows.append([
                row['graph_id'],
                row['encoding'],
                row['best_k'],
                row['lower_bound'],
                row['proof'],
                comparative_outcome(row, best_sources),
                row['timeout'],
            ])
        emit(
            tag + '_results',
            [
                'Graph',
                'Encoding',
                'UB',
                'LB',
                'Proof',
                'Comparative result',
                'Timeout',
            ],
            result_rows,
            title,
        )

        pair_summary_rows = []
        for first_encoding, second_encoding in combinations(categories, 2):
            pair_name = (
                tag + '_pair_' + first_encoding + '_' + second_encoding
            )
            pair_rows = select(
                runs,
                'encoding',
                (first_encoding, second_encoding),
                'p2b',
                pair_name,
                lambda row: row['method'] == method,
                exploratory=exploratory,
            )
            proven_timed_rows = [
                row for row in pair_rows
                if row['proof'] == 'optimal'
                and row['total_time'] is not None
            ]
            matched_timed_rows = common(
                proven_timed_rows,
                'encoding',
                (first_encoding, second_encoding),
                lambda row: stratum(row, 'p2b'),
            )
            first_runtimes = [
                row['total_time']
                for row in matched_timed_rows
                if row['encoding'] == first_encoding
            ]
            second_runtimes = [
                row['total_time']
                for row in matched_timed_rows
                if row['encoding'] == second_encoding
            ]
            pair_summary_rows.append([
                first_encoding,
                second_encoding,
                len(pair_rows) // 2,
                len(matched_timed_rows) // 2,
                median(first_runtimes),
                median(second_runtimes),
            ])

        emit(
            tag + '_pairs',
            [
                'A',
                'B',
                'Common cases',
                'Both optimal timed',
                'A median',
                'B median',
            ],
            pair_summary_rows,
            title + '; pairwise intersections are independent of other backends.',
        )

def main():
    part2b(load_runs())
    print('Backend reports written')

if __name__ == '__main__':
    main()