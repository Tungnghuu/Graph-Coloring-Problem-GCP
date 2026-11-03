from pathlib import Path
from src.utils.graph_io import read_col
from src.encoding import SATEncoding, POPEncoding, POHPEncoding
from src.chromatic_number.repeated_sat import RepeatedSAT
from src.chromatic_number.incremental_sat import IncrementalSAT
from src.chromatic_number.bound_methods.combined import CombinedBounds

# Read graph
col_path = Path("data") / "instances" / "DSJC125.9.col"
graph = read_col(str(col_path))

# Create encoding
encoding = POHPEncoding()

# Lower and upper bounds
bounds = CombinedBounds()
print(RepeatedSAT._find_bounds(graph, bounds))

# Create result file name
graph_name = col_path.stem
results_path = Path("results") / "exp" / f"{graph_name}_res.csv"

# Run RepeatedSAT
solver = IncrementalSAT()

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

# from .../.../Graph-Coloring-Problem-GCP use "python -m experiment.exp_1"
# not .../.../Graph-Coloring-Problem-GCP/experiment/...