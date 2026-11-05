from pathlib import Path
from src.utils.graph_io import read_col
from src.encoding import SATEncoding, POPEncoding, POHPEncoding, CPLEXCPEncoding, GurobiILPEncoding, CPLEXMIPEncoding
from src.chromatic_number.repeated_sat import RepeatedSAT
from src.chromatic_number.incremental_sat import IncrementalSAT
from src.chromatic_number.binarySearch_sat import BinarySearchSAT
from src.chromatic_number.bound_methods.combined import CombinedBounds

# Read graph
col_path = Path("data") / "250" / "DSJC250_9.col"
graph = read_col(str(col_path))

# Create encoding
encoding = CPLEXCPEncoding()

# Lower and upper bounds
bounds = CombinedBounds()
print(RepeatedSAT._find_bounds(graph, bounds))

# Create result file name
graph_name = col_path.stem
results_path = Path("results") / "exp" / f"{graph_name}_res.csv"

# Run RepeatedSAT
solver = RepeatedSAT()

chromatic_number = solver.find_chromatic_number(
    graph=graph,
    encoding=encoding,
    bounds_method=bounds,
    results_path=str(results_path),
    time_limit=20,
)

print("Graph:", graph_name)
print("Chromatic number:", chromatic_number)
print("Results saved to:", results_path)