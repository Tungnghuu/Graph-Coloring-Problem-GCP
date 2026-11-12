from pathlib import Path

from src.benchmark.single_benchmark import run_benchmark
from src.encoding import POHPEncoding, POPEncoding, SATEncoding
from src.utils.graph_io import read_col

PROJECT_DIR = Path(__file__).resolve().parent
GRAPH_PATH = PROJECT_DIR / "data" / "250" / "anna.col"

# List the encodings that this benchmark will compare.
ENCODINGS = {
    "SAT": SATEncoding,
    "POP": POPEncoding,
    "POHP": POHPEncoding,
}
COLOR_COUNT = 15
TIME_LIMIT = 5


def main():
    # Load the graph once so each encoding uses the same input.
    graph = read_col(str(GRAPH_PATH))

    # Run and print the measurements for each encoding.
    for name, encoding_type in ENCODINGS.items():
        result = run_benchmark(
            encoding_type(),
            graph,
            COLOR_COUNT,
            time_limit=TIME_LIMIT,
        )
        print(name)
        for metric, value in result.items():
            print(f"{metric}: {value}")
        print()


if __name__ == "__main__":
    main()
