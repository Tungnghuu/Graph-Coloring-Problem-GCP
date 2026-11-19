if __package__:
    from .reports_common import (
        FIG, ROOT, TABLES,
        grouped, median, number, read_csv
    )
else:
    from reports_common import (
        FIG, ROOT, TABLES,
        grouped, median, number, read_csv
    )

def conclusions(runs):
    verified_run_count = sum(
        row['metadata_verified']
        for row in runs
    )
    findings = [
        '# Analysis findings',
        (
            f'Input run records: {len(runs)}. '
            f'Verified metadata: {verified_run_count}.'
        ),
        (
            'Primary comparisons require verified metadata. Historical '
            'outputs have exploratory labels; they cannot establish a '
            'controlled ranking.'
        ),
        (
            'Legacy POP logs are not evidence for the new partial-order '
            'implementation. See rerun_needed.csv.'
        ),
        (
            'Pairwise runtime tables use common proven-optimal runs. '
            'Runtime plots may also include the best-observed feasible '
            'result; k can differ across methods or encodings. Timeout and '
            'missing outcomes remain in coverage; timeout duration is not '
            'solution time.'
        ),
        (
            'Best observed means the lowest recorded valid best_k among '
            'methods or encodings in the same graph comparison; it is '
            'comparative only and does not prove optimality. A timeout '
            'alone is not evidence that its current k is feasible.'
        ),
        (
            'Historical lower bounds can omit the original bound '
            'calculation. Historical solve times may include setup. '
            'No historical wall-clock values are reconstructed.'
        ),
        (
            'Gap uses (UB-LB)/UB and only recorded certified bounds; '
            'missing values are not zero. SAT/ILP/CP quality is assessed '
            'separately from speed.'
        ),
        (
            'Each membership table identifies included/excluded source '
            'files. No fastest-repeat selection is performed.'
        ),
        (
            'For k sweeps, inspect status-specific peaks and intervals in '
            'p3_summary.csv. Runtime need not be monotonic in k; each '
            'bucket has only one representative.'
        ),
        (
            'Expected coverage requires --expected; without it completely '
            'absent runs cannot be counted.'
        ),
    ]

    findings_path = FIG.parent / 'findings.md'
    findings_path.write_text('\n\n'.join(findings) + '\n')

def empirical_findings():
    findings_lines = ['## Observations from generated tables']

    part1_summary_paths = sorted(TABLES.glob('*_summary.csv'))
    for summary_path in part1_summary_paths:
        if not summary_path.stem.startswith('p1_'):
            continue

        summary_rows = read_csv(summary_path)
        if not summary_rows:
            continue

        if 'exploratory' in summary_path.stem:
            cohort_label = 'Exploratory, not a controlled conclusion'
        else:
            cohort_label = 'Verified cohort'
        findings_lines.append(
            f'{cohort_label} ({summary_path.stem}):'
        )

        timing_metrics = (
            'Encoding median',
            'Solve median',
            'Total median',
        )
        for metric in timing_metrics:
            rows_with_measurement = [
                row for row in summary_rows
                if number(row.get(metric)) is not None
            ]
            if not rows_with_measurement:
                continue

            fastest_row = min(
                rows_with_measurement,
                key=lambda row: number(row[metric]),
            )
            findings_lines.append(
                f'- Lowest {metric}: {fastest_row["Encoding"]}, '
                f'{float(fastest_row[metric]):.6g} s; '
                'common optimal/best-observed timed '
                f'n={fastest_row["Optimal/best-observed timed n"]}.'
            )

        findings_lines.append(
            'These medians apply only to the matched proven or '
            'best-observed subset. k may differ; use timeout/feasible '
            'counts and IQR alongside speed; no overall winner follows '
            'from speed alone.'
        )

    method_table_paths = sorted(TABLES.glob('p2a_*_methods.csv'))
    for method_table_path in method_table_paths:
        method_rows = read_csv(method_table_path)
        if not method_rows:
            continue

        method_summaries = []
        for row in method_rows:
            method_summaries.append(
                f'{row["Method"]}: optimal={row["Optimal %"]}%, '
                f'timeout={row["Timeout"]}/{row["Runs"]}, '
                f'median attempts={row["Median attempts"]}'
            )

        findings_lines.append(
            f'{method_table_path.stem}: '
            + '; '.join(method_summaries)
            + '.'
        )

    pair_table_paths = sorted(TABLES.glob('p2b_*_pairs.csv'))
    for pair_table_path in pair_table_paths:
        pair_rows = read_csv(pair_table_path)
        for row in pair_rows:
            both_runs_were_timed = number(row['Both optimal timed'])
            if not both_runs_were_timed:
                continue

            findings_lines.append(
                f'{pair_table_path.stem}: {row["A"]} vs {row["B"]}, '
                f'common cases={row["Common cases"]}, '
                f'both proven timed={row["Both optimal timed"]}; '
                f'medians={row["A median"]} / {row["B median"]} s. '
                'Pairwise samples can differ; do not combine these into '
                'a universal ordering.'
            )

    sweep_path = ROOT / 'processed' / 'k_sweep.csv'
    sweep_rows = read_csv(sweep_path)
    sweeps_by_graph = grouped(
        sweep_rows,
        lambda row: row['graph_id'],
    )

    for graph_id, graph_rows in sorted(sweeps_by_graph.items()):
        measured_rows = []
        for row in graph_rows:
            runtime = number(row['total_time'])
            if runtime is None:
                continue

            row['total_time'] = runtime
            measured_rows.append(row)

        measured_rows.sort(key=lambda row: float(row['k']))
        if not measured_rows:
            continue

        peak_row = max(
            measured_rows,
            key=lambda row: row['total_time'],
        )

        slower_at_smaller_k = 0
        for previous_row, next_row in zip(
            measured_rows,
            measured_rows[1:],
        ):
            if previous_row['total_time'] > next_row['total_time']:
                slower_at_smaller_k += 1
        adjacent_pair_count = max(0, len(measured_rows) - 1)

        timeout_color_counts = [
            int(float(row['k']))
            for row in measured_rows
            if row['status'] == 'TIMEOUT'
        ]
        if timeout_color_counts:
            timeout_range = (
                min(timeout_color_counts),
                max(timeout_color_counts),
            )
            timeout_range_text = str(timeout_range)
        else:
            timeout_range_text = 'none recorded'

        findings_lines.append(
            f'{graph_id}: largest observed runtime at '
            f'k={peak_row["k"]}, status={peak_row["status"]}, '
            f't={peak_row["total_time"]:.6g}s. Smaller k was slower in '
            f'{slower_at_smaller_k}/{adjacent_pair_count} adjacent '
            'observed pairs. Timeout k range: '
            f'{timeout_range_text}; range does not imply every interior '
            'k timed out.'
        )

        for status in ('SAT', 'UNSAT'):
            solve_times = []
            for row in measured_rows:
                solve_time = number(row['solving_time'])
                if row['status'] == status and solve_time is not None:
                    solve_times.append(float(solve_time))

            if solve_times:
                findings_lines.append(
                    f'- {status}: n={len(solve_times)}, '
                    f'median recorded solve={median(solve_times):.6g}s. '
                    'This is descriptive; different k and censoring '
                    'preclude a significance claim.'
                )

    findings_lines.append(
        'Size, density, k and structure can all affect difficulty. '
        'Single-graph bucket samples and historical metadata gaps prevent '
        'claims about all large graphs or native solver families.'
    )

    findings_path = FIG.parent / 'findings.md'
    with findings_path.open('a') as findings_file:
        findings_file.write('\n\n' + '\n\n'.join(findings_lines) + '\n')
