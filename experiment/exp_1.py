from pathlib import Path
from src.utils.graph_io import read_col
from src.encoding import POHPEncoding, SATEncoding
from src.chromatic_number.repeated_sat import RepeatedSAT

ROOT_DIR = Path(__file__).resolve().parent.parent

# Read graph
col_path = ROOT_DIR / "data" / "instances" / "anna.col"
graph = read_col(str(col_path))

# Create encoding
encoding = POHPEncoding()

# Lower and upper bounds
bounds = [1, 15]

# Create result file name
graph_name = col_path.stem
results_path = ROOT_DIR / "results" / f"{graph_name}_res.csv"

# Run RepeatedSAT
solver = RepeatedSAT()

chromatic_number = solver.find_chromatic_number(
    graph=graph,
    encoding=encoding,
    bounds_method=bounds,
    results_path=str(results_path),
)

print("Graph:", graph_name)
print("Chromatic number:", chromatic_number)
print("Results saved to:", results_path)

# from .../.../Graph-Coloring-Problem-GCP use "python -m experiment.exp_1"
# not .../.../Graph-Coloring-Problem-GCP/experiment/...