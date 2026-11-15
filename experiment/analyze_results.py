"""Aggregate benchmark CSV files and produce reproducible summary tables/plots.

Usage:
    python experiment/analyze_results.py
    python experiment/analyze_results.py --results results --output analysis
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REQUIRED_COLUMNS = {
    "method",
    "encoding",
    "k",
    "status",
    "num_variables",
    "num_clauses",
    "valid_coloring",
    "bounds_time",
    "encoding_time",
    "solving_time",
    "total_time",
}
METHOD_LABELS = {
    "BinarySearchSAT": "Binary",
    "RepeatedSolver": "Repeated",
    "IncrementalSAT": "Incremental",
}
ENCODING_LABELS = {
    "SATEncoding": "SAT",
    "POPEncoding": "POP",
    "POHPEncoding": "POHP",
    "GurobiILPEncoding": "Gurobi ILP",
    "CPLEXMIPEncoding": "CPLEX MIP",
    "CPLEXCPEncoding": "CPLEX CP",
}
FILE_ENCODING_LABELS = {
    "SAT": "SAT",
    "POP": "POP",
    "POHP": "POHP",
    "Gurobi_ILP": "Gurobi ILP",
    "CPLEX_MIP": "CPLEX MIP",
    "CPLEX_CP": "CPLEX CP",
}


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def read_graph_sizes(data_dir: Path) -> dict[str, tuple[int, int, str]]:
    sizes = {}
    for path in data_dir.rglob("*.col"):
        vertices = edges = None
        with path.open(encoding="utf-8", errors="replace") as stream:
            for line in stream:
                parts = line.split()
                if len(parts) >= 3 and parts[0].lower() == "p":
                    vertices, edges = int(parts[-2]), int(parts[-1])
                    break
        if vertices is not None and edges is not None:
            sizes[path.stem] = (vertices, edges, path.parent.name)
    return sizes


def median_or_blank(values: list[float]) -> str:
    return f"{statistics.median(values):.6g}" if values else ""


def iqr(values: list[float]) -> str:
    if len(values) < 2:
        return ""
    quartiles = statistics.quantiles(values, n=4, method="inclusive")
    return f"{quartiles[2] - quartiles[0]:.6g}"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_attempts(results_dir: Path, graph_sizes: dict[str, tuple[int, int, str]]) -> tuple[list[dict], list[dict]]:
    attempts = []
    coverage = []
    for path in sorted(results_dir.rglob("*.csv")):
        relative = path.relative_to(results_dir)
        parts = relative.parts
        if len(parts) < 3:
            continue
        method_folder, _, bucket = parts[:3]
        graph_name = path.stem.removesuffix("_res")
        graph_name = graph_name.rsplit("_", 1)[0] if "_" in graph_name else graph_name
        # Encoding names contain underscores, so identify the graph from the data set.
        candidates = [name for name in graph_sizes if path.stem.startswith(name + "_")]
        if candidates:
            graph_name = max(candidates, key=len)
        graph_info = graph_sizes.get(graph_name, (None, None, bucket))

        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            columns = set(reader.fieldnames or [])
            if not REQUIRED_COLUMNS.issubset(columns):
                raise ValueError(f"{path}: missing columns {sorted(REQUIRED_COLUMNS - columns)}")
            rows = list(reader)
        if not rows:
            coverage.append({
                "graph": graph_name, "method_folder": method_folder,
                "encoding_file": path.stem, "bucket": bucket,
                "encoding": next(
                    (label for suffix, label in FILE_ENCODING_LABELS.items()
                     if path.stem.endswith("_" + suffix + "_res")), ""),
                "coverage_status": "header_only", "attempts": 0,
            })
            continue
        for row in rows:
            row.update({
                "graph": graph_name,
                "bucket": graph_info[2],
                "vertices": graph_info[0],
                "edges": graph_info[1],
                "method_label": METHOD_LABELS.get(row["method"], row["method"]),
                "encoding_label": ENCODING_LABELS.get(row["encoding"], row["encoding"]),
                "k": int(row["k"]),
                "num_variables": int(float(row["num_variables"])),
                "num_clauses": int(float(row["num_clauses"])),
                "valid_coloring": parse_bool(row["valid_coloring"]),
                "bounds_time": float(row["bounds_time"]),
                "encoding_time": float(row["encoding_time"]),
                "solving_time": float(row["solving_time"]),
                "total_time": float(row["total_time"]),
                "encoding_timeout": row["status"] == "TIMEOUT"
                and int(float(row["num_variables"])) == 0,
            })
            attempts.append(row)
        statuses = {row["status"] for row in rows}
        coverage.append({
            "graph": graph_name, "method_folder": method_folder,
            "encoding_file": path.stem, "bucket": bucket,
            "encoding": next(
                (label for suffix, label in FILE_ENCODING_LABELS.items() if path.stem.endswith("_" + suffix + "_res")),
                "",
            ),
            "coverage_status": (
                "partial" if "TIMEOUT" in statuses and "SAT" in statuses else
                "timeout" if "TIMEOUT" in statuses else "completed"
            ),
            "attempts": len(rows),
        })
    return attempts, coverage


def aggregate(attempts: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in attempts:
        groups[(row["graph"], row["bucket"], row["method_label"], row["encoding_label"])].append(row)
    output = []
    for (graph, bucket, method, encoding), rows in sorted(groups.items()):
        valid = [row["k"] for row in rows if row["valid_coloring"]]
        unsat = [row["k"] for row in rows if row["status"] == "UNSAT"]
        upper = min(valid) if valid else ""
        lower = max(unsat) + 1 if unsat else ""
        optimal = bool(upper != "" and lower != "" and upper == lower)
        times = {key: [row[key] for row in rows] for key in
                 ("encoding_time", "solving_time", "total_time", "num_variables", "num_clauses")}
        output.append({
            "graph": graph, "bucket": bucket, "method": method, "encoding": encoding,
            "vertices": rows[0]["vertices"], "edges": rows[0]["edges"],
            "attempts": len(rows), "timeout": any(row["status"] == "TIMEOUT" for row in rows),
            "encoding_timeout": any(row["encoding_timeout"] for row in rows),
            "valid_coloring_found": bool(valid), "best_valid_upper_bound": upper,
            "proved_lower_bound": lower, "proven_optimal": optimal,
            "optimality_gap": (
                upper - lower if upper != "" and lower != "" else ""
            ),
            "encoding_time_median": median_or_blank(times["encoding_time"]),
            "encoding_time_iqr": iqr(times["encoding_time"]),
            "encoding_time_total": sum(times["encoding_time"]),
            "solving_time_median": median_or_blank(times["solving_time"]),
            "solving_time_iqr": iqr(times["solving_time"]),
            "solving_time_total": sum(times["solving_time"]),
            "total_time_median": median_or_blank(times["total_time"]),
            "total_time_iqr": iqr(times["total_time"]),
            "total_time_total": sum(times["total_time"]),
            "bounds_time_once": sum(row["bounds_time"] for row in rows),
            "variables_median": median_or_blank(times["num_variables"]),
            "clauses_median": median_or_blank(times["num_clauses"]),
            "variables_min": min(times["num_variables"]),
            "variables_max": max(times["num_variables"]),
            "clauses_min": min(times["num_clauses"]),
            "clauses_max": max(times["num_clauses"]),
        })
    return output


def summary(rows: list[dict], keys: tuple[str, ...]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    result = []
    for group, values in sorted(groups.items()):
        result.append({
            **dict(zip(keys, group)),
            "graphs": len(values),
            "timeouts": sum(bool(row["timeout"]) for row in values),
            "encoding_time_median": median_or_blank([float(row["encoding_time_median"]) for row in values if row["encoding_time_median"]]),
            "solving_time_median": median_or_blank([float(row["solving_time_median"]) for row in values if row["solving_time_median"]]),
            "total_time_median": median_or_blank([float(row["total_time_median"]) for row in values if row["total_time_median"]]),
            "variables_median": median_or_blank([float(row["variables_median"]) for row in values if row["variables_median"]]),
            "clauses_median": median_or_blank([float(row["clauses_median"]) for row in values if row["clauses_median"]]),
            "valid_colorings": sum(bool(row["valid_coloring_found"]) for row in values),
            "proven_optimal": sum(bool(row["proven_optimal"]) for row in values),
            "attempts_mean": (
                statistics.mean(row["attempts"] for row in values) if values else ""
            ),
            "best_upper_bound_median": median_or_blank(
                [float(row["best_valid_upper_bound"]) for row in values
                 if row["best_valid_upper_bound"] != ""]
            ),
        })
    return result


def paired_rows(rows: list[dict], methods: set[str], encodings: set[str]) -> list[dict]:
    groups = defaultdict(dict)
    for row in rows:
        if row["method"] in methods and row["encoding"] in encodings:
            groups[(row["graph"], row["bucket"], row["method"])][row["encoding"]] = row
    result = []
    for (graph, bucket, method), values in groups.items():
        if set(values) != encodings:
            continue
        result.append({
            "graph": graph, "bucket": bucket, "method": method,
            **{f"{encoding}_total_time": values[encoding]["total_time_total"]
               for encoding in sorted(encodings)},
            **{f"{encoding}_best_upper_bound": values[encoding]["best_valid_upper_bound"]
               for encoding in sorted(encodings)},
            **{f"{encoding}_optimality_gap": values[encoding]["optimality_gap"]
               for encoding in sorted(encodings)},
            **{f"{encoding}_proven_optimal": values[encoding]["proven_optimal"]
               for encoding in sorted(encodings)},
        })
    return sorted(result, key=lambda row: (row["bucket"], row["graph"], row["method"]))


def backend_rows(rows: list[dict], method: str = "Binary") -> list[dict]:
    return paired_rows(
        [row for row in rows if row["method"] == method],
        {method},
        {"SAT", "Gurobi ILP", "CPLEX MIP", "CPLEX CP"},
    )


def backend_comparison_summary(
    rows: list[dict], graph_sizes: dict[str, tuple[int, int, str]]
) -> list[dict]:
    encodings = {"SAT", "Gurobi ILP", "CPLEX MIP", "CPLEX CP"}
    result = []
    for bucket in sorted({info[2] for info in graph_sizes.values()}):
        expected = {name for name, info in graph_sizes.items() if info[2] == bucket}
        selected = [row for row in rows
                    if row["method"] == "Binary" and row["bucket"] == bucket
                    and row["encoding"] in encodings]
        by_encoding = defaultdict(list)
        for row in selected:
            by_encoding[row["encoding"]].append(row)
        common = set.intersection(
            *(set(row["graph"] for row in values) for values in by_encoding.values())
        ) if by_encoding and len(by_encoding) == len(encodings) else set()
        for encoding in sorted(encodings):
            values = by_encoding[encoding]
            result.append({
                "bucket": bucket,
                "backend": encoding,
                "common_graphs": len(common),
                "available_runs": len(values),
                "missing_runs": len(expected) - len(values),
                "solved_valid": sum(row["valid_coloring_found"] for row in values),
                "proven_optimal": sum(row["proven_optimal"] for row in values),
                "timeouts": sum(row["timeout"] for row in values),
                "runtime_median": median_or_blank(
                    [float(row["total_time_total"]) for row in values]
                ),
                "optimality_gap_median": median_or_blank(
                    [float(row["optimality_gap"]) for row in values
                     if row["optimality_gap"] != ""]
                ),
            })
    return result


def coverage_summary(
    coverage: list[dict], graph_sizes: dict[str, tuple[int, int, str]]
) -> list[dict]:
    expected_encodings = {
        "Binary": set(ENCODING_LABELS.values()),
        "Repeated": set(ENCODING_LABELS.values()),
        "Incremental": {"SAT", "POP", "POHP"},
    }
    present = {
        (METHOD_LABELS.get(row["method_folder"], row["method_folder"]), row["bucket"],
         row["graph"], row.get("encoding", ""))
        for row in coverage
    }
    buckets = sorted({info[2] for info in graph_sizes.values()})
    result = []
    for method, encodings in expected_encodings.items():
        for bucket in buckets:
            graphs = [name for name, info in graph_sizes.items() if info[2] == bucket]
            expected = {(method, bucket, graph, encoding)
                        for graph in graphs for encoding in encodings}
            rows = [row for row in coverage
                    if METHOD_LABELS.get(row["method_folder"], row["method_folder"]) == method
                    and row["bucket"] == bucket]
            result.append({
                "method": method, "bucket": bucket, "expected_runs": len(expected),
                "files": len(rows),
                "completed": sum(row["coverage_status"] == "completed" for row in rows),
                "partial": sum(row["coverage_status"] == "partial" for row in rows),
                "missing": len(expected - present),
                "header_only": sum(row["coverage_status"] == "header_only" for row in rows),
                "timeout": sum(row["coverage_status"] == "timeout" for row in rows),
            })
    return result


def plot_box(rows: list[dict], value: str, title: str, output: Path, log_scale: bool = False) -> None:
    groups = defaultdict(list)
    for row in rows:
        if row[value] != "":
            groups[(row["encoding"], row["bucket"])].append(float(row[value]))
    labels, values = zip(*[(f"{encoding}\n{bucket}", data) for (encoding, bucket), data in sorted(groups.items())])
    figure, axis = plt.subplots(figsize=(max(8, len(labels) * 0.8), 5))
    axis.boxplot(values, tick_labels=labels, showmeans=False)
    axis.set_title(title)
    axis.set_ylabel("seconds" if "time" in value else value)
    if log_scale:
        axis.set_yscale("log")
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_scatter(rows: list[dict], value: str, title: str, output: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 5))
    for encoding in sorted({row["encoding"] for row in rows}):
        selected = [row for row in rows if row["encoding"] == encoding and row[value] != ""]
        axis.scatter([row["vertices"] for row in selected], [float(row[value]) for row in selected],
                     label=encoding, alpha=0.7)
    axis.set_xlabel("vertices")
    axis.set_ylabel=value
    axis.set_title(title)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_timeout_heatmap(rows: list[dict], output: Path) -> None:
    encodings = sorted({row["encoding"] for row in rows})
    buckets = sorted({row["bucket"] for row in rows})
    matrix = []
    for encoding in encodings:
        line = []
        for bucket in buckets:
            selected = [row for row in rows
                        if row["encoding"] == encoding and row["bucket"] == bucket]
            line.append(100 * sum(bool(row["timeout"]) for row in selected) / len(selected)
                        if selected else math.nan)
        matrix.append(line)
    figure, axis = plt.subplots(figsize=(max(7, len(buckets) * 1.2), 4))
    image = axis.imshow(matrix, cmap="Reds", vmin=0, vmax=100, aspect="auto")
    axis.set_xticks(range(len(buckets)), buckets)
    axis.set_yticks(range(len(encodings)), encodings)
    axis.set_xlabel("graph-size bucket")
    axis.set_title("Timeout rate by encoding and bucket (%)")
    figure.colorbar(image, ax=axis, label="% timeout")
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_attempts_runtime(rows: list[dict], output: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 5))
    for method in sorted({row["method"] for row in rows}):
        selected = [row for row in rows if row["method"] == method]
        axis.scatter([row["attempts"] for row in selected],
                     [float(row["total_time_total"]) for row in selected],
                     label=method, alpha=0.65)
    axis.set_xlabel("solver attempts (k values)")
    axis.set_ylabel("total wall-clock time (seconds)")
    axis.set_yscale("log")
    axis.set_title("Attempts versus total runtime")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_paired(rows: list[dict], encodings: list[str], title: str, output: Path) -> None:
    figure, axis = plt.subplots(figsize=(max(8, len(rows) * 0.3), 5))
    for index, row in enumerate(rows):
        values = [float(row[f"{encoding}_total_time"]) for encoding in encodings]
        axis.plot(range(len(encodings)), values, color="0.75", linewidth=0.7)
        axis.scatter(range(len(encodings)), values, s=12)
    axis.set_xticks(range(len(encodings)), encodings)
    axis.set_yscale("log")
    axis.set_ylabel("total wall-clock time (seconds)")
    axis.set_title(f"{title} (n={len(rows)} paired graphs)")
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_best_colors(rows: list[dict], encodings: list[str], output: Path) -> None:
    figure, axis = plt.subplots(figsize=(max(8, len(rows) * 0.3), 5))
    for index, row in enumerate(rows):
        for encoding_index, encoding in enumerate(encodings):
            value = row[f"{encoding}_best_upper_bound"]
            if value == "":
                continue
            color = "tab:green" if row[f"{encoding}_proven_optimal"] else "tab:orange"
            axis.scatter(encoding_index, float(value), color=color, s=18)
    axis.set_xticks(range(len(encodings)), encodings)
    axis.set_ylabel("best valid number of colors")
    axis.set_title("Best colors on paired graphs (green=proven, orange=timeout/feasible)")
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_backend_outcomes(rows: list[dict], encodings: list[str], output: Path) -> None:
    optimal = [sum(bool(row[f"{encoding}_proven_optimal"]) for row in rows)
               for encoding in encodings]
    feasible = [sum(row[f"{encoding}_best_upper_bound"] != "" and
                    not row[f"{encoding}_proven_optimal"] for row in rows)
                for encoding in encodings]
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(encodings, optimal, label="Optimal")
    axis.bar(encodings, feasible, bottom=optimal, label="Feasible only")
    axis.set_ylabel("paired graph count")
    axis.set_title("Backend outcome comparison")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_backend_boxplot(rows: list[dict], output: Path) -> None:
    groups = defaultdict(list)
    for row in rows:
        groups[row["encoding"]].append(float(row["total_time_total"]))
    available = [(encoding, values) for encoding, values in sorted(groups.items()) if values]
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.boxplot([values for _, values in available],
                 tick_labels=[encoding for encoding, _ in available], showmeans=False)
    axis.set_yscale("log")
    axis.set_ylabel("total wall-clock time (seconds)")
    axis.set_title("Backend runtime distribution (Binary SAT search)")
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_performance_profile(rows: list[dict], encodings: list[str], output: Path) -> None:
    ratios = {encoding: [] for encoding in encodings}
    for row in rows:
        times = {encoding: float(row[f"{encoding}_total_time"]) for encoding in encodings}
        fastest = min(times.values())
        for encoding, value in times.items():
            ratios[encoding].append(value / fastest)
    figure, axis = plt.subplots(figsize=(8, 5))
    for encoding, values in ratios.items():
        values.sort()
        axis.step(values, [(index + 1) / len(values) for index in range(len(values))],
                  where="post", label=encoding)
    axis.set_xscale("log")
    axis.set_xlabel("runtime / fastest runtime")
    axis.set_ylabel("proportion of paired graphs")
    axis.set_title("Dolan-Moré performance profile")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_optimality_gap(rows: list[dict], encodings: list[str], output: Path) -> None:
    gaps = defaultdict(list)
    for row in rows:
        for encoding in encodings:
            upper = row[f"{encoding}_best_upper_bound"]
            if upper == "":
                continue
            # A missing proof is conservatively displayed as an unknown gap.
            gap = row[f"{encoding}_optimality_gap"]
            if gap != "":
                gaps[encoding].append(float(gap))
    figure, axis = plt.subplots(figsize=(9, 5))
    available = [(encoding, values) for encoding, values in gaps.items() if values]
    if available:
        axis.boxplot([values for _, values in available],
                     tick_labels=[encoding for encoding, _ in available], showmeans=False)
    axis.set_ylabel("upper bound - proved lower bound")
    axis.set_title("Optimality gap on paired runs with both bounds")
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("analysis"))
    args = parser.parse_args()
    graph_sizes = read_graph_sizes(args.data)
    attempts, coverage = load_attempts(args.results, graph_sizes)
    graph_rows = aggregate(attempts)
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "attempts_normalized.csv", attempts)
    write_csv(args.output / "graph_aggregates.csv", graph_rows)
    write_csv(args.output / "coverage.csv", coverage_summary(coverage, graph_sizes))
    write_csv(args.output / "encoding_summary.csv", summary(graph_rows, ("encoding", "bucket")))
    write_csv(args.output / "method_summary.csv", summary(graph_rows, ("method", "bucket")))
    write_csv(args.output / "backend_summary.csv", summary(
        [row for row in graph_rows
         if row["method"] == "Binary"
         and row["encoding"] in {"SAT", "Gurobi ILP", "CPLEX MIP", "CPLEX CP"}],
        ("encoding", "bucket"),
    ))

    sat_rows = [row for row in graph_rows if row["encoding"] in {"SAT", "POP", "POHP"}]
    search_pairs = paired_rows(sat_rows, {"Binary", "Repeated", "Incremental"},
                               {"SAT", "POP", "POHP"})
    backend_pair_rows = backend_rows(graph_rows)
    backend_summary_rows = backend_comparison_summary(graph_rows, graph_sizes)
    write_csv(args.output / "encoding_paired.csv", paired_rows(
        sat_rows, {"Binary"}, {"SAT", "POP", "POHP"}))
    write_csv(args.output / "search_paired.csv", search_pairs)
    write_csv(args.output / "backend_paired.csv", backend_pair_rows)
    write_csv(args.output / "backend_comparison_summary.csv", backend_summary_rows)
    plot_box(sat_rows, "encoding_time_median", "Encoding time by encoding and bucket",
             args.output / "encoding_time_boxplot.png", log_scale=True)
    plot_box(sat_rows, "solving_time_median", "Solving time by encoding and bucket",
             args.output / "solving_time_boxplot.png", log_scale=True)
    plot_box(sat_rows, "total_time_total", "Total time by encoding and bucket",
             args.output / "total_time_boxplot.png", log_scale=True)
    plot_scatter(sat_rows, "variables_median", "Formula variables vs graph size",
                 args.output / "variables_vs_vertices.png")
    plot_scatter(sat_rows, "clauses_median", "Formula clauses vs graph size",
                 args.output / "clauses_vs_vertices.png")
    plot_timeout_heatmap(sat_rows, args.output / "timeout_heatmap.png")
    plot_attempts_runtime(sat_rows, args.output / "attempts_vs_runtime.png")
    plot_paired(
        [row for row in search_pairs if row["method"] == "Binary"],
        ["SAT", "POP", "POHP"],
        "Paired encoding runtime comparison",
        args.output / "encoding_paired_runtime.png",
    )
    plot_best_colors(
        [row for row in search_pairs if row["method"] == "Binary"],
        ["SAT", "POP", "POHP"],
        args.output / "best_colors_paired.png",
    )
    plot_paired(
        backend_pair_rows,
        ["SAT", "Gurobi ILP", "CPLEX MIP", "CPLEX CP"],
        "Paired SAT/ILP/CP runtime comparison",
        args.output / "backend_runtime_boxplot.png",
    )
    plot_backend_outcomes(
        backend_pair_rows,
        ["SAT", "Gurobi ILP", "CPLEX MIP", "CPLEX CP"],
        args.output / "backend_outcomes.png",
    )
    plot_backend_boxplot(
        [row for row in graph_rows
         if row["method"] == "Binary"
         and row["encoding"] in {"SAT", "Gurobi ILP", "CPLEX MIP", "CPLEX CP"}],
        args.output / "backend_time_boxplot.png",
    )
    plot_performance_profile(
        backend_pair_rows,
        ["SAT", "Gurobi ILP", "CPLEX MIP", "CPLEX CP"],
        args.output / "performance_profile.png",
    )
    plot_optimality_gap(
        backend_pair_rows,
        ["SAT", "Gurobi ILP", "CPLEX MIP", "CPLEX CP"],
        args.output / "optimality_gap.png",
    )
    print(f"Analyzed {len(attempts)} attempts and {len(graph_rows)} graph-level runs.")
    print(f"Outputs written to {args.output.resolve()}")


if __name__ == "__main__":
    main()
