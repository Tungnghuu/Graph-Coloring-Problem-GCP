import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = PROJECT_DIR / "results" / "benchmark_summary.csv"
DEFAULT_OUTPUT = PROJECT_DIR / "results" / "analysis"


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def read_attempt_rows(directory: Path) -> list[dict]:
    rows = []
    for path in sorted(directory.glob("*.csv")):
        parts = path.stem.rsplit("_", 2)
        if len(parts) != 3:
            continue
        graph, method, encoding = parts
        attempts = read_rows(path)
        if not attempts:
            continue
        total_time = sum(number(row, "total_time") or 0 for row in attempts)
        final = next(
            (row for row in reversed(attempts) if row.get("status") == "SAT"),
            attempts[-1],
        )
        method_name = method.removesuffix("SAT").lower()
        if method_name == "binarysearch":
            method_name = "binary"
        rows.append({
            "graph": graph,
            "method": method_name,
            "encoding": encoding.removesuffix("Encoding"),
            "status": final.get("status", ""),
            "chromatic_number": final.get("k", ""),
            "valid_coloring": final.get("valid_coloring", ""),
            "elapsed_time": total_time,
        })
    return rows


def number(row: dict, key: str) -> float | None:
    value = row.get(key, "")
    try:
        return float(value) if value != "" else None
    except ValueError:
        return None


def aggregate(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        elapsed = number(row, "elapsed_time")
        if elapsed is not None:
            groups[(row["method"], row["encoding"])].append(elapsed)

    result = []
    for (method, encoding), values in sorted(groups.items()):
        result.append({
            "method": method,
            "encoding": encoding,
            "graphs": len(values),
            "mean_seconds": statistics.fmean(values),
            "median_seconds": statistics.median(values),
            "min_seconds": min(values),
            "max_seconds": max(values),
        })
    return result


def speedups(rows: list[dict]) -> list[dict]:
    by_case = {
        (row["graph"], row["encoding"], row["method"]): number(row, "elapsed_time")
        for row in rows
    }
    result = []
    for (graph, encoding, method), elapsed in sorted(
        (key, value) for key, value in by_case.items() if value is not None
    ):
        baseline = by_case.get((graph, encoding, "repeated"))
        if baseline is None or elapsed == 0:
            continue
        result.append({
            "graph": graph,
            "encoding": encoding,
            "method": method,
            "repeated_seconds": baseline,
            "method_seconds": elapsed,
            "speedup_vs_repeated": baseline / elapsed,
        })
    return result


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(output: Path, rows: list[dict], summary: list[dict]) -> None:
    valid = sum(row.get("valid_coloring") == "True" for row in rows)
    statuses = defaultdict(int)
    for row in rows:
        statuses[row.get("status", "")] += 1

    lines = [
        "# Benchmark analysis",
        "",
        f"- Runs: {len(rows)}",
        f"- Valid colorings: {valid}/{len(rows)}",
        f"- Statuses: {dict(sorted(statuses.items()))}",
        "",
        "## Aggregate timing",
        "",
        "| Method | Encoding | Graphs | Mean (s) | Median (s) | Min (s) | Max (s) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['method']} | {row['encoding']} | {row['graphs']} | "
            f"{row['mean_seconds']:.6f} | {row['median_seconds']:.6f} | "
            f"{row['min_seconds']:.6f} | {row['max_seconds']:.6f} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot(rows: list[dict], output: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise RuntimeError(
            "Matplotlib is required for plots. Install it with: "
            "python -m pip install matplotlib"
        ) from error

    groups = defaultdict(list)
    for row in rows:
        elapsed = number(row, "elapsed_time")
        if elapsed is not None:
            groups[f"{row['method']}/{row['encoding']}"].append(elapsed)
    labels = sorted(groups)
    values = [statistics.fmean(groups[label]) for label in labels]

    figure, axis = plt.subplots(figsize=(max(8, len(labels) * 1.2), 5))
    axis.bar(labels, values)
    axis.set_ylabel("Mean elapsed time (seconds)")
    axis.set_title("Graph coloring benchmark")
    axis.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    figure.savefig(output / "mean_elapsed_time.png", dpi=160)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze benchmark CSV results.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--attempts-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    rows = read_rows(args.input)
    if args.attempts_dir is not None:
        rows.extend(read_attempt_rows(args.attempts_dir))
    if not rows:
        raise ValueError(f"No benchmark rows found in {args.input}")
    summary = aggregate(rows)
    speedup = speedups(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "timing_summary.csv", summary)
    write_csv(args.output_dir / "speedup_vs_repeated.csv", speedup)
    write_report(args.output_dir / "REPORT.md", rows, summary)
    if args.plot:
        plot(rows, args.output_dir)
    print(f"Analyzed {len(rows)} runs. Results: {args.output_dir}")


if __name__ == "__main__":
    main()
