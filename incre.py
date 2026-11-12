from src.benchmark.experiment_runner import PROJECT_DIR, run_experiment

SIZE_FOLDERS = ["100_or_less", "250", "500", "750", "1000"]
RESULTS_DIR = PROJECT_DIR / "results" / "Incremental" / "with_bm"

TIME_LIMIT = 30
ENCODING_TIME_LIMIT = 30
TOTAL_TIME_LIMIT = None

def main():
    for size_folders in SIZE_FOLDERS:
        dataset_dir = PROJECT_DIR / "data" / size_folders
        graph_paths = list(dataset_dir.glob("*.col"))

        run_experiment(
            "incremental",
            graph_paths,
            RESULTS_DIR,
            time_limit=TIME_LIMIT,
            encoding_time_limit=ENCODING_TIME_LIMIT,
            total_time_limit=TOTAL_TIME_LIMIT,
        )

if __name__ == "__main__":
    main()