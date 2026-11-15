# Graph Coloring Problem

## Benchmark analysis

The reproducible analysis pipeline is in
[`experiment/analyze_results.py`](experiment/analyze_results.py). It reads the
per-`k` CSV files under `results/`, aggregates them at graph/method/encoding
level, and writes tables and PNG figures without counting repeated
`bounds_time` values.

```powershell
python experiment\analyze_results.py --results results --data data --output analysis
```

Generated files include:

- `attempts_normalized.csv`: validated attempt-level data;
- `graph_aggregates.csv`: one row per graph, search method and encoding;
- `coverage.csv`: expected, completed, partial, missing, header-only and
  timeout runs by method and graph-size bucket;
- `encoding_summary.csv`, `method_summary.csv` and `backend_summary.csv`;
- `encoding_paired.csv`, `search_paired.csv`, `backend_paired.csv` and
  `backend_comparison_summary.csv` for paired comparisons, missing runs and
  optimality gaps;
- separate box plots for encoding, solving and total wall-clock time, plus
  variable/clause size plots, timeout heatmap, best-color comparison,
  backend outcomes, Dolan-Moré performance profile and gap distribution.

`TIMEOUT` rows with zero variables and clauses are classified as encoding
timeouts. A valid coloring found before a timeout is retained as a best-known
upper bound and is not reported as a proven chromatic number. Header-only CSV
files are reported as `header_only`, never as timeouts.