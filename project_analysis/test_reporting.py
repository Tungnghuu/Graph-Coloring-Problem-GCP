"""Regression checks for empty plots and stale report archives."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from project_analysis import reports
from project_analysis.run_all import archive_outputs


class ReportingTests(unittest.TestCase):
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
            self.assertTrue((Path(tmp)/'zero.pdf').exists())
            self.assertEqual(reports.FIGURE_STATUS[1]['status'], 'created')

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
