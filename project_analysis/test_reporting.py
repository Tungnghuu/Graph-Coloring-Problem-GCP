from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from project_analysis import reports
from project_analysis import analysis_core
from project_analysis.run_all import archive_outputs

class ReportingTests(unittest.TestCase):
    def test_graph_presentation_labels_are_english(self):
        _, title, caption = reports.figure_presentation(
            'p1_Repeated_exploratory_encoding_time'
        )

        self.assertIn('Encoding time comparison', title)
        self.assertIn('Historical data', caption)
        self.assertEqual(reports.AXIS_LABELS['encoding_time'], 'Encoding time (s)')

    def test_figure_filenames_use_english_metric_names(self):
        slugs = {
            'encoding_time': 'encoding_time',
            'solving_time': 'solving_time',
            'total_time': 'total_time',
            'timeout': 'timeout_rate',
            'num_variables': 'variables',
            'num_clauses': 'clauses',
            'paired_time': 'runtime_by_graph',
            'best_colors': 'best_colors',
            'attempts_time': 'attempts_vs_runtime',
            'solver_calls_time': 'solver_calls_vs_runtime',
            'outcomes': 'solution_outcomes',
            'profile': 'performance_profile',
            'gap': 'optimality_gap',
        }

        for metric, english_slug in slugs.items():
            filename, _, _ = reports.figure_presentation(
                f'p1_Repeated_exploratory_{metric}'
            )
            self.assertEqual(filename, f'p1_{english_slug}_repeated')

        verified_filename, _, _ = reports.figure_presentation(
            'p1_Repeated_encoding_time'
        )
        self.assertEqual(
            verified_filename,
            'p1_encoding_time_repeated_verified',
        )

    def test_empty_artists_do_not_make_a_chart(self):
        fig, ax = reports.plt.subplots()
        ax.plot([], [])
        ax.scatter([], [])
        self.assertFalse(reports.has_plotted_data(fig))
        reports.plt.close(fig)

    def test_placeholder_is_skipped_but_real_zero_is_saved(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(reports, 'FIG', Path(tmp)), patch.object(reports, 'FIGURE_STATUS', []):
            reports.no_data('Missing evidence')
            reports.save('empty')
            self.assertFalse((Path(tmp)/'empty.png').exists())
            self.assertEqual(reports.FIGURE_STATUS[0]['status'], 'skipped')
            reports.plt.figure()
            reports.plt.plot([1], [0], marker='o')
            reports.save('zero')
            self.assertTrue((Path(tmp)/'zero.png').exists())
            self.assertFalse((Path(tmp)/'zero.pdf').exists())
            self.assertEqual(reports.FIGURE_STATUS[1]['status'], 'created')

    def test_analysis_tables_write_csv_without_latex(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            analysis_core.table('sample', ['Value'], [[1]], 'Sample', output)

            self.assertTrue((output/'sample.csv').exists())
            self.assertFalse((output/'sample.tex').exists())

    def test_part3_single_graph_plots_components_but_multi_graph_only_total(self):
        rows = [
            {
                'graph_id': 'graph-a.col',
                'graph': 'graph-a.col',
                'k': 2,
                'status': 'SAT',
                'encoding_time': 1.0,
                'solving_time': 2.0,
                'total_time': 3.0,
            },
            {
                'graph_id': 'graph-a.col',
                'graph': 'graph-a.col',
                'k': 3,
                'status': 'TIMEOUT',
                'encoding_time': 4.0,
                'solving_time': 5.0,
                'total_time': 9.0,
            },
        ]
        inventory = [{'schema': 'k_sweep', 'source': 'sweep.csv',
                      'graph_id': 'graph-a.col', 'rows': '2'}]
        captured = {}

        def capture_figure(name):
            captured[name] = [
                line.get_label() for line in reports.plt.gca().lines
                if not line.get_label().startswith('_')
            ]
            reports.plt.close()

        with (
            patch.object(reports, 'ROOT', Path('.')),
            patch.object(reports, 'read_csv', side_effect=[rows, inventory]),
            patch.object(reports, 'emit'),
            patch.object(reports, 'save', side_effect=capture_figure),
        ):
            reports.part3()

        self.assertEqual(
            captured['p3_graph-a'],
            ['Encoding time', 'Solving time', 'Total runtime'],
        )
        self.assertEqual(captured['p3_runtime_k'], ['graph-a.col'])

    def test_multi_graph_k_sweep_uses_requested_folder_order(self):
        groups = ['dense', '1000', '750', '500', '250', '100_or_less']
        rows = [
            {
                'graph_id': group + '\\example.col',
                'graph': 'example.col',
                'k': 2,
                'status': 'SAT',
                'encoding_time': 1.0,
                'solving_time': 2.0,
                'total_time': 3.0,
            }
            for group in groups
        ]
        inventory = [{'schema': 'k_sweep', 'source': 'sweep.csv',
                      'graph_id': row['graph_id'], 'rows': '1'} for row in rows]
        multi_graph_legend = []

        def capture_figure(name):
            if name == 'p3_runtime_k':
                multi_graph_legend.extend(
                    line.get_label() for line in reports.plt.gca().lines
                )
            reports.plt.close()

        with (
            patch.object(reports, 'ROOT', Path('.')),
            patch.object(reports, 'read_csv', side_effect=[rows, inventory]),
            patch.object(reports, 'emit'),
            patch.object(reports, 'save', side_effect=capture_figure),
        ):
            reports.part3()

        self.assertEqual(
            multi_graph_legend,
            [
                '100_or_less\\example.col',
                '250\\example.col',
                '500\\example.col',
                '750\\example.col',
                '1000\\example.col',
                'dense\\example.col',
            ],
        )

    def test_graph_figure_name_does_not_create_nested_folders(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(reports, 'FIG', Path(tmp)), patch.object(reports, 'FIGURE_STATUS', []):
            reports.plt.figure()
            reports.plt.plot([1], [1])
            reports.save(r'p3_1000\inithx_i_1')
            self.assertTrue(
                (Path(tmp)/'p3_runtime_by_k_1000_inithx_i_1.png').exists()
            )
            self.assertFalse((Path(tmp)/'p3_runtime_by_k_1000').is_dir())

    def test_p2a_attempt_plot_keeps_long_runs_on_symlog_scale(self):
        rows = [
            {
                'source': method,
                'graph': 'example.col',
                'graph_id': 'dense/example.col',
                'group': 'dense',
                'comparison_config': 'historical',
                'backend': 'PySAT',
                'encoding': 'SAT',
                'method': method,
                'proof': 'unknown',
                'timeout': True,
                'total_time': 7000,
                'attempts': 8,
                'solver_calls': 8,
                'best_k': None,
                'lower_bound': None,
            }
            for method in ('Incremental', 'Repeated', 'Binary')
        ]
        scales = []
        maximum_runtimes = []

        def capture_plot(name):
            if name.endswith('_attempts_time'):
                axis = reports.plt.gca()
                scales.append(axis.get_yscale())
                maximum_runtimes.append(
                    max(
                        offset[1]
                        for collection in axis.collections
                        for offset in collection.get_offsets()
                    )
                )
            reports.plt.close()

        selections = [rows, [], rows, [], rows, []]
        with (
            patch.object(reports, 'select', side_effect=selections),
            patch.object(reports, 'boxes'),
            patch.object(reports, 'heat'),
            patch.object(reports, 'paired'),
            patch.object(reports, 'emit'),
            patch.object(reports, 'save', side_effect=capture_plot),
        ):
            reports.part2a(rows, exploratory=True)

        self.assertEqual(scales, ['symlog'] * 3)
        self.assertEqual(maximum_runtimes, [7000] * 3)

    def test_p2b_uses_method_specific_encoding_sets(self):
        encodings = reports.BACKENDS
        rows = [
            {
                'source': encoding,
                'graph': 'example.col',
                'graph_id': 'dense/example.col',
                'group': 'dense',
                'comparison_config': 'historical',
                'backend': encoding,
                'encoding': encoding,
                'method': method,
                'proof': 'optimal',
                'timeout': False,
                'total_time': 1.0,
                'best_k': 3,
                'lower_bound': 3,
                'gap': None,
            }
            for method in reports.P2B_METHODS
            for encoding in encodings
        ]
        selections = []

        def capture_selection(runs, key, categories, part, name, predicate=lambda r: True, *args, **kwargs):
            if part == 'p2b' and key == 'encoding' and name.startswith('p2b_') and name.endswith('_exploratory'):
                method = name[len('p2b_'):-len('_exploratory')]
                selections.append((method, tuple(categories)))
            return [
                row for row in runs
                if row['encoding'] in categories and predicate(row)
            ]

        with (
            patch.object(reports, 'select', side_effect=capture_selection),
            patch.object(reports, 'boxes'),
            patch.object(reports, 'heat'),
            patch.object(reports, 'paired'),
            patch.object(reports, 'emit'),
            patch.object(reports, 'save', side_effect=lambda _name: reports.plt.close()),
            patch.object(reports, 'performance_profile', return_value={}),
        ):
            reports.part2b(rows, exploratory=True)

        self.assertEqual(
            selections,
            [
                ('Incremental', reports.P2B_ENCODINGS),
                ('Repeated', reports.BACKENDS),
                ('Binary', reports.BACKENDS),
            ],
        )

    def test_p2b_keeps_graphs_without_commercial_solver_runs(self):
        rows = [
            {
                'source': 'sat-only',
                'graph_id': 'graph-present-in-sat-results.col',
                'comparison_config': 'historical',
                'encoding': 'SAT',
                'method': 'Incremental',
                'backend': 'PySAT',
            },
            {
                'source': 'gurobi-only',
                'graph_id': 'graph-present-in-sat-results.col',
                'comparison_config': 'historical',
                'encoding': 'Gurobi_ILP',
                'method': 'Repeated',
                'backend': 'Gurobi',
            },
        ]

        with (
            patch.object(reports, 'clean_runs', return_value=rows),
            patch.object(reports, 'emit'),
        ):
            selected = reports.select(
                rows,
                'encoding',
                reports.P2B_ENCODINGS,
                'p2b',
                'graph-retention',
                exploratory=True,
                require_common=False,
            )

        self.assertEqual([row['source'] for row in selected], ['sat-only'])
        self.assertEqual(
            selected[0]['graph_id'],
            'graph-present-in-sat-results.col',
        )

    def test_p2b_best_observed_is_not_reported_as_proven_optimal(self):
        rows = [
            {
                'source': encoding,
                'graph_id': 'dense/example.col',
                'comparison_config': 'historical',
                'method': 'Repeated',
                'encoding': encoding,
                'proof': 'feasible',
                'best_k': colors,
            }
            for encoding, colors in (('A', 11), ('B', 10), ('C', 11))
        ]
        best_sources = reports.best_observed_sources(rows)

        self.assertEqual(best_sources, {'B'})
        self.assertEqual(
            [reports.comparative_outcome(row, best_sources) for row in rows],
            ['feasible', 'best_observed', 'feasible'],
        )

        timeout_only = dict(
            rows[0], source='timeout-only', best_k=None, proof='unknown'
        )
        self.assertEqual(
            reports.comparative_outcome(timeout_only, best_sources),
            'unknown',
        )

    def test_p2b_runtime_profile_includes_best_observed_runs(self):
        encodings = reports.P2B_ENCODINGS
        rows = [
            {
                'source': encoding,
                'graph_id': 'dense/example.col',
                'comparison_config': 'historical',
                'method': 'Repeated',
                'encoding': encoding,
                'proof': 'feasible' if encoding == 'SAT' else 'optimal',
                'total_time': 2.0 if encoding == 'SAT' else 1.0,
            }
            for encoding in encodings
        ]

        profile = reports.performance_profile(rows, encodings, {'SAT'})

        self.assertEqual(profile['SAT'][0], (1, 0.0))
        self.assertEqual(profile['SAT'][-1][1], 1.0)

    def test_best_observed_comparison_can_compare_methods(self):
        rows = [
            {
                'source': method,
                'graph_id': 'dense/example.col',
                'comparison_config': 'historical',
                'backend': 'PySAT',
                'encoding': 'SAT',
                'method': method,
                'proof': 'feasible',
                'best_k': colors,
            }
            for method, colors in (('Incremental', 10), ('Repeated', 11), ('Binary', 12))
        ]

        self.assertEqual(
            reports.best_observed_sources(rows, 'p2a'),
            {'Incremental'},
        )

    def test_archive_keeps_old_outputs_out_of_current_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'figures').mkdir()
            (root/'figures'/'old.pdf').write_bytes(b'old output')
            archive_outputs(root)
            self.assertFalse((root/'figures').exists())
            archived=list((root/'archive').glob('*/figures/old.pdf'))
            self.assertEqual(len(archived), 1)
            self.assertEqual(archived[0].read_bytes(), b'old output')

if __name__ == '__main__':
    unittest.main()