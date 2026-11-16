from src.benchmark.experiment_runner import PROJECT_DIR, run_experiment
from src.encoding import POHPEncoding, POPEncoding, SATEncoding

SIZE_FOLDERS = ["dense"]
RESULTS_DIR = PROJECT_DIR / "results" / "Repeated" / "with_bm"

TIME_LIMIT = 30
ENCODING_TIME_LIMIT = 30
TOTAL_TIME_LIMIT = None

def main():
    for size_folder in SIZE_FOLDERS:
        dataset_dir = PROJECT_DIR / "data" / size_folder
        graph_paths = list(dataset_dir.glob("*.col"))

        run_experiment(
            "repeated",
            graph_paths,
            RESULTS_DIR,
            time_limit=TIME_LIMIT,
            encoding_time_limit=ENCODING_TIME_LIMIT,
            total_time_limit=TOTAL_TIME_LIMIT,
            encoding_specs=(
                ("SAT", SATEncoding, None),
                ("POP", POPEncoding, None),
                ("POHP", POHPEncoding, None),
            ),
        )

if __name__ == "__main__":
    main()