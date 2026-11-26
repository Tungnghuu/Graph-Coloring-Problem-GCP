from pathlib import Path
import argparse
import shutil

if __package__:
    import importlib
    from . import reports
    from . import analysis_core as core
    preprocessing = importlib.import_module(".01_preprocess", __package__)
else:
    import importlib
    import reports
    import analysis_core as core
    preprocessing = importlib.import_module("01_preprocess")

def clear_outputs(output_directory):
    for name in ('figures', 'tables', 'figure_status.csv'):
        path = output_directory / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Preprocess experiment results and create all reports.'
    )
    parser.add_argument(
        '--source',
        type=Path,
        action='append',
        help='Input directory; repeat this option to add more directories.',
    )
    parser.add_argument(
        '--data',
        type=Path,
        default=core.PROJECT / 'data',
        help='Folder containing the graph files.',
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=core.ROOT,
        help='Folder where processed files and reports are written.',
    )
    parser.add_argument(
        '--expected',
        type=Path,
        help='Optional CSV manifest of expected runs.',
    )
    parser.add_argument(
        '--part1-method',
        choices=('Repeated', 'Binary', 'Incremental'),
        default='Repeated',
        help='Search method to use in Part 1.',
    )

    report_mode = parser.add_mutually_exclusive_group()
    report_mode.add_argument(
        '--verified-only',
        action='store_true',
        help='Require verified metadata and skip unavailable figures.',
    )
    report_mode.add_argument(
        '--exploratory',
        action='store_true',
        help='Allow historical results and mark them as exploratory.',
    )

    return parser.parse_args()

def main():
    args = parse_arguments()

    reports.ROOT = args.output
    reports.FIG = args.output / 'outputs' / 'figures'
    reports.TABLES = args.output / 'outputs' / 'tables'

    input_sources = args.source or [
        core.PROJECT / 'results',
        core.ROOT / 'raw_results',
    ]

    runs, attempts, issues = preprocessing.preprocess(
        input_sources,
        args.data,
        args.output / 'processed',
        args.expected,
    )

    clear_outputs(args.output / 'outputs')
    reports.FIGURE_STATUS.clear()

    reports.overview(runs, issues)

    exploratory = not args.verified_only

    reports.part1(runs, args.part1_method, exploratory)
    reports.part2a(runs, exploratory)
    reports.part2b(runs, exploratory=exploratory)
    reports.part3()

    reports.write_figure_status()

    membership_rows = []
    membership_files = sorted(reports.TABLES.glob('*_membership.csv'))
    for membership_file in membership_files:
        rows = core.read_csv(membership_file)
        for row in rows:
            membership_rows.append(
                dict(comparison=membership_file.stem, **row)
            )

    membership_fields = [
        'comparison',
        'Source',
        'Graph',
        'Included',
        'Reason',
    ]
    core.write_csv(
        args.output / 'processed' / 'comparison_membership.csv',
        membership_rows,
        membership_fields,
    )

    print(
        f'{len(runs)} runs, {len(attempts)} attempts, '
        f'{len(issues)} notices. Output: {args.output}'
    )

if __name__ == '__main__':
    main()