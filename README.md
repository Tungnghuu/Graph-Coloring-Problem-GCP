# Graph Coloring Project

This project studies the graph coloring problem. It compares SAT encodings
(SAT, POP, and POHP) and includes ILP and CP solver implementations.
The experiments measure solving results, formula size, and runtime.

## Project structure

```text
Graph-Coloring-Problem/
|-- main.py
|-- data/
|-- src/
|   |-- benchmark/
|   |-- chromatic_number/
|   |-- encoding/
|   |-- solver/
|   |-- utils/
|   |-- bin.py
|   |-- exp_1.py
|   |-- exp_2.py
|   |-- incre.py
|   `-- rep.py
|-- project_analysis/
|   |-- 01_preprocess.py
|   |-- 02_overview_tables.py
|   |-- 03_part1_encodings.py
|   |-- 04_part2a_sat_methods.py
|   |-- 05_part2b_solver_families.py
|   |-- 06_part3_k_sweep.py
|   |-- analysis_core.py
|   `-- reports.py
|-- results/
|-- output/
|-- lib/
`-- requirements.txt
```

## Main folders and files

- `main.py`: runs a small benchmark for one graph and compares the three SAT
  encodings.
- `data/`: input graph files. The subfolders group graphs by size or type.
- `src/`: the main graph coloring and experiment code.
  - `benchmark/`: runs benchmarks and saves experiment results.
  - `chromatic_number/`: searches for a graph's minimum number of colors.
  - `encoding/`: builds SAT, ILP, and CP models.
  - `solver/`: connects models to solver tools.
  - `utils/`: reads graphs and checks or displays colorings.
  - `bin.py`, `incre.py`, and `rep.py`: run binary, incremental, and repeated
    search experiments.
  - `exp_1.py` and `exp_2.py`: run graph coloring experiment scripts.
- `project_analysis/`: processes experiment results and creates tables,
  figures, and written findings. The numbered files divide the analysis into
  sections.
- `results/`: saved experiment data.
- `output/`: report figures and tables.
- `lib/`: bundled JavaScript and style files used by the project.
- `requirements.txt`: lists the Python packages used by the project.
