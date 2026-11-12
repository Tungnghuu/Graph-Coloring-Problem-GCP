import csv
from pathlib import Path

class ResultsWriter:
    FIELDNAMES = [
        "method",
        "encoding",
        "k",
        "status",
        "num_variables",
        "num_clauses",
        "valid_coloring",
        "bounds_time",
        "encoding_time",
        "solving_time",
        "total_time",
    ]

    def __init__(self, col_file_path):
        # Use the requested path when it already points to a CSV file
        path = Path(col_file_path)
        if path.suffix.lower() == ".csv":
            self.file_path = path
        else:
            self.file_path = Path("results") / f"{path.stem}.csv"

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.FIELDNAMES)
            writer.writeheader()

    def save(self, result):
        with open(self.file_path, "a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.FIELDNAMES)
            writer.writerow(result)
