from src.encoding import SATEncoding, POPEncoding, POHPEncoding
from src.benchmark.single_benchmark import run_benchmark
from src.utils.graph_io import read_col

graph = read_col("data/instances/anna.col")

encodings = {
    "SAT": SATEncoding(),
    "POP": POPEncoding(),
    "POHP": POHPEncoding(),
}

k = 10

for name, encoding in encodings.items():
    result = run_benchmark(encoding, graph, k, time_limit = 5)

    print(f"{name}")
    for metric, value in result.items():
        print(f"{metric}: {value}")
    print("\n")