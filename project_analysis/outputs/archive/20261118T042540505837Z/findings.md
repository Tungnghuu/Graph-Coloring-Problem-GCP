# Analysis findings

Input run records: 1191. Verified metadata: 0.

Primary comparisons require verified metadata. Historical outputs have exploratory labels; they cannot establish a controlled ranking.

Legacy POP logs are not evidence for the new partial-order implementation. See rerun_needed.csv.

Pairwise runtime tables use common proven-optimal runs. Runtime plots may also include the best-observed feasible result; k can differ across methods or encodings. Timeout and missing outcomes remain in coverage; timeout duration is not solution time.

Best observed means the lowest recorded valid best_k among methods or encodings in the same graph comparison; it is comparative only and does not prove optimality. A timeout alone is not evidence that its current k is feasible.

Historical lower bounds can omit the original bound calculation. Historical solve times may include setup. No historical wall-clock values are reconstructed.

Gap uses (UB-LB)/UB and only recorded certified bounds; missing values are not zero. SAT/ILP/CP quality is assessed separately from speed.

Each membership table identifies included/excluded source files. No fastest-repeat selection is performed.

For k sweeps, inspect status-specific peaks and intervals in p3_summary.csv. Runtime need not be monotonic in k; each bucket has only one representative.

Expected coverage requires --expected; without it completely absent runs cannot be counted.


## Observations from generated tables

Exploratory, not a controlled conclusion (p1_Repeated_exploratory_summary):

- Lowest Encoding median: POP, 0.419216 s; common optimal/best-observed timed n=60.

- Lowest Solve median: POHP, 0.621839 s; common optimal/best-observed timed n=60.

- Lowest Total median: SAT, 1.91059 s; common optimal/best-observed timed n=60.

These medians apply only to the matched proven or best-observed subset. k may differ; use timeout/feasible counts and IQR alongside speed; no overall winner follows from speed alone.

p2a_POHP_exploratory_methods: Binary: optimal=7.042253521126761%, timeout=33/71, median attempts=2.0; Incremental: optimal=7.042253521126761%, timeout=35/71, median attempts=2.0; Repeated: optimal=7.042253521126761%, timeout=35/71, median attempts=2.0.

p2a_POP_exploratory_methods: Binary: optimal=7.6923076923076925%, timeout=28/65, median attempts=2.0; Incremental: optimal=7.6923076923076925%, timeout=29/65, median attempts=2.0; Repeated: optimal=7.6923076923076925%, timeout=28/65, median attempts=2.0.

p2a_SAT_exploratory_methods: Binary: optimal=7.6923076923076925%, timeout=28/65, median attempts=2.0; Incremental: optimal=7.6923076923076925%, timeout=30/65, median attempts=2.0; Repeated: optimal=7.6923076923076925%, timeout=27/65, median attempts=2.0.

p2b_Binary_exploratory_pairs: SAT vs POP, common cases=72, both proven timed=6; medians=0.08903675008332357 / 0.05523315002210438 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: SAT vs POHP, common cases=72, both proven timed=6; medians=0.08903675008332357 / 0.1344393499311991 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: SAT vs Gurobi_ILP, common cases=72, both proven timed=6; medians=0.08903675008332357 / 0.961106650007423 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: SAT vs CPLEX_MIP, common cases=72, both proven timed=6; medians=0.08903675008332357 / 1.0633469999884255 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: SAT vs CPLEX_CP, common cases=72, both proven timed=5; medians=0.04799390025436878 / 0.14253260020632297 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: POP vs POHP, common cases=72, both proven timed=6; medians=0.05523315002210438 / 0.1344393499311991 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: POP vs Gurobi_ILP, common cases=72, both proven timed=6; medians=0.05523315002210438 / 0.961106650007423 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: POP vs CPLEX_MIP, common cases=72, both proven timed=6; medians=0.05523315002210438 / 1.0633469999884255 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: POP vs CPLEX_CP, common cases=72, both proven timed=5; medians=0.014675900107249618 / 0.14253260020632297 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: POHP vs Gurobi_ILP, common cases=78, both proven timed=6; medians=0.1344393499311991 / 0.961106650007423 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: POHP vs CPLEX_MIP, common cases=78, both proven timed=6; medians=0.1344393499311991 / 1.0633469999884255 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: POHP vs CPLEX_CP, common cases=78, both proven timed=5; medians=0.02064469992183149 / 0.14253260020632297 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: Gurobi_ILP vs CPLEX_MIP, common cases=78, both proven timed=9; medians=4.613147799856961 / 2.3333651999710128 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: Gurobi_ILP vs CPLEX_CP, common cases=78, both proven timed=9; medians=4.613147799856961 / 0.153762900037691 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: CPLEX_MIP vs CPLEX_CP, common cases=78, both proven timed=8; medians=2.111938249960076 / 0.1492644500103779 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Incremental_exploratory_pairs: SAT vs POP, common cases=70, both proven timed=5; medians=0.05720769986510277 / 0.06407460000264109 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Incremental_exploratory_pairs: SAT vs POHP, common cases=70, both proven timed=5; medians=0.05720769986510277 / 0.19395450002048165 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Incremental_exploratory_pairs: POP vs POHP, common cases=71, both proven timed=5; medians=0.06407460000264109 / 0.19395450002048165 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: SAT vs POP, common cases=75, both proven timed=6; medians=0.0539783999483916 / 0.06434209999861196 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: SAT vs POHP, common cases=75, both proven timed=6; medians=0.0539783999483916 / 0.08501714999874821 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: SAT vs Gurobi_ILP, common cases=75, both proven timed=6; medians=0.0539783999483916 / 0.7614594999831752 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: SAT vs CPLEX_MIP, common cases=75, both proven timed=6; medians=0.0539783999483916 / 0.7255736999795772 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: SAT vs CPLEX_CP, common cases=75, both proven timed=5; medians=0.04019699990749359 / 0.20339829997101333 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POP vs POHP, common cases=75, both proven timed=6; medians=0.06434209999861196 / 0.08501714999874821 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POP vs Gurobi_ILP, common cases=75, both proven timed=6; medians=0.06434209999861196 / 0.7614594999831752 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POP vs CPLEX_MIP, common cases=75, both proven timed=6; medians=0.06434209999861196 / 0.7255736999795772 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POP vs CPLEX_CP, common cases=75, both proven timed=5; medians=0.028382799995597452 / 0.20339829997101333 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POHP vs Gurobi_ILP, common cases=78, both proven timed=6; medians=0.08501714999874821 / 0.7614594999831752 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POHP vs CPLEX_MIP, common cases=78, both proven timed=6; medians=0.08501714999874821 / 0.7255736999795772 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POHP vs CPLEX_CP, common cases=78, both proven timed=5; medians=0.03556769998976961 / 0.20339829997101333 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: Gurobi_ILP vs CPLEX_MIP, common cases=78, both proven timed=9; medians=6.064277799989213 / 2.60371579999628 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: Gurobi_ILP vs CPLEX_CP, common cases=78, both proven timed=9; medians=6.064277799989213 / 0.2272324000223307 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: CPLEX_MIP vs CPLEX_CP, common cases=78, both proven timed=8; medians=1.8340323999946122 / 0.22241915000631707 s. Pairwise samples can differ; do not combine these into a universal ordering.

1000\inithx_i_1.col: largest observed runtime at k=744, status=SAT, t=119.697s. Smaller k was slower in 365/863 adjacent observed pairs. Timeout k range: (24, 53); range does not imply every interior k timed out.

- SAT: n=811, median recorded solve=8.90951s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=24, median recorded solve=0.202854s. This is descriptive; different k and censoring preclude a significance claim.

100_or_less\david.col: largest observed runtime at k=86, status=SAT, t=0.334972s. Smaller k was slower in 31/86 adjacent observed pairs. Timeout k range: none recorded; range does not imply every interior k timed out.

- SAT: n=77, median recorded solve=0.028534s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=10, median recorded solve=0.00427605s. This is descriptive; different k and censoring preclude a significance claim.

250\anna.col: largest observed runtime at k=136, status=SAT, t=1.37158s. Smaller k was slower in 50/137 adjacent observed pairs. Timeout k range: none recorded; range does not imply every interior k timed out.

- SAT: n=128, median recorded solve=0.0600058s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=10, median recorded solve=0.0074665s. This is descriptive; different k and censoring preclude a significance claim.

500\DSJC500_1.col: largest observed runtime at k=496, status=SAT, t=33.1942s. Smaller k was slower in 226/499 adjacent observed pairs. Timeout k range: (6, 14); range does not imply every interior k timed out.

- SAT: n=486, median recorded solve=2.51544s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=5, median recorded solve=0.0225102s. This is descriptive; different k and censoring preclude a significance claim.

750\homer.col: largest observed runtime at k=517, status=SAT, t=24.4718s. Smaller k was slower in 253/560 adjacent observed pairs. Timeout k range: none recorded; range does not imply every interior k timed out.

- SAT: n=549, median recorded solve=1.4736s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=12, median recorded solve=0.0513523s. This is descriptive; different k and censoring preclude a significance claim.

dense\flat300_20_0.col: largest observed runtime at k=30, status=TIMEOUT, t=34.1785s. Smaller k was slower in 127/299 adjacent observed pairs. Timeout k range: (12, 39); range does not imply every interior k timed out.

- SAT: n=261, median recorded solve=2.08805s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=11, median recorded solve=0.0740125s. This is descriptive; different k and censoring preclude a significance claim.

Size, density, k and structure can all affect difficulty. Single-graph bucket samples and historical metadata gaps prevent claims about all large graphs or native solver families.


## Skipped figures

No placeholder images are exported. See figure_status.csv for every figure.
- p2a_solver_calls_vs_runtime_sat: No matched observations with the required metric; see membership tables.
- p2a_solver_calls_vs_runtime_pop: No matched observations with the required metric; see membership tables.
- p2a_solver_calls_vs_runtime_pohp: No matched observations with the required metric; see membership tables.
