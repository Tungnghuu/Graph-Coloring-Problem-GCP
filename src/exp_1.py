from src.benchmark.experiment_runner import PROJECT_DIR, run_experiment
from src.encoding import POHPEncoding

GRAPH_PATH = PROJECT_DIR / "data" / "250" / "DSJC250_9.col"
RESULTS_DIR = PROJECT_DIR / "results" / "exp"
TIME_LIMIT = 20
ENCODING_TIME_LIMIT = 30

def main():
    run_experiment(
        "incremental",
        [GRAPH_PATH],
        RESULTS_DIR,
        time_limit=TIME_LIMIT,
        encoding_time_limit=ENCODING_TIME_LIMIT,
        encoding_specs=(("POHP", POHPEncoding, None),),
        group_results_by_dataset=False,
    )

if __name__ == "__main__":
    main()