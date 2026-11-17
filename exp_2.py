import csv

from src.benchmark.experiment_runner import PROJECT_DIR
from src.benchmark.single_benchmark import run_benchmark
from src.encoding import POHPEncoding
from src.utils.graph_io import read_col

DATA_DIR = PROJECT_DIR / "data"
RESULTS_DIR = PROJECT_DIR / "results" / "exp"
TIME_LIMIT = 30

SELECTED_GRAPHS = {
    "750": "homer.col",
    "1000": "inithx_i_1.col",
}

def main():
    graph_paths = []
    for folder_name, graph_name in SELECTED_GRAPHS.items():
        graph_path = DATA_DIR / folder_name / graph_name
        if not graph_path.is_file():
            raise FileNotFoundError(f"Selected graph not found: {graph_path}")
        graph_paths.append((folder_name, graph_name, graph_path))

    if not graph_paths:
        raise FileNotFoundError(f"No graphs selected under {DATA_DIR}")

    for folder_name, graph_name, graph_path in graph_paths:
        print(f"Loading {folder_name}/{graph_name}")
        graph = read_col(str(graph_path))

        results_folder = RESULTS_DIR / folder_name
        results_folder.mkdir(parents=True, exist_ok=True)
        results_path = results_folder / f"{graph_path.stem}_POHP_k_sweep.csv"

        with results_path.open("w", newline="") as results_file:
            writer = csv.writer(results_file)
            writer.writerow([
                "dataset",
                "graph",
                "k",
                "status",
                "num_variables",
                "num_clauses",
                "encoding_time",
                "solving_time",
                "total_time",
                "valid_coloring",
            ])

            for k in range(graph.n, 0, -1):
                result = run_benchmark(
                    POHPEncoding(),
                    graph,
                    k,
                    time_limit=TIME_LIMIT,
                )
                writer.writerow([
                    folder_name,
                    graph_name,
                    result["k"],
                    result["status"],
                    result["num_variables"],
                    result["num_clauses"],
                    result["encoding_time"],
                    result["solving_time"],
                    result["total_time"],
                    result["valid_coloring"],
                ])
                results_file.flush()

                print(
                    f"k={k}, status={result['status']}, "
                    f"encoding={result['encoding_time']:.3f}s, "
                    f"solving={result['solving_time']:.3f}s"
                )

        print(f"Saved results to {results_path}")

if __name__ == "__main__":
    main()