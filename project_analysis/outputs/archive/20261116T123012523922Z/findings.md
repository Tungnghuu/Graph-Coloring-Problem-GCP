# Analysis findings

Input run records: 1191. Verified metadata: 0.

Primary comparisons require verified metadata. Historical outputs have exploratory labels; they cannot establish a controlled ranking.

Legacy POP logs are not evidence for the new partial-order implementation. See rerun_needed.csv.

Runtime tables compare common proven-optimal runs. Timeout and missing outcomes remain in coverage; timeout duration is not solution time.

Historical lower bounds can omit the original bound calculation. Historical solve times may include setup. No historical wall-clock values are reconstructed.

Gap uses (UB-LB)/UB and only recorded certified bounds; missing values are not zero. SAT/ILP/CP quality is assessed separately from speed.

Each membership table identifies included/excluded source files. No fastest-repeat selection is performed.

For k sweeps, inspect status-specific peaks and intervals in p3_summary.csv. Runtime need not be monotonic in k; each bucket has only one representative.

Expected coverage requires --expected; without it completely absent runs cannot be counted.


## Observations from generated tables

Exploratory, not a controlled conclusion (p1_Repeated_exploratory_summary):

- Lowest Encoding median: POP, 0.0135309 s; common proven timed n=6.

- Lowest Solve median: SAT, 0.0228996 s; common proven timed n=6.

- Lowest Total median: SAT, 0.0539784 s; common proven timed n=6.

These medians apply only to the matched proven subset. Use timeout/feasible counts and IQR alongside speed; no overall winner follows from speed alone.

p2a_POHP_exploratory_methods: Binary: optimal=7.042253521126761%, timeout=33/71, median attempts=2; Incremental: optimal=7.042253521126761%, timeout=35/71, median attempts=2; Repeated: optimal=7.042253521126761%, timeout=35/71, median attempts=2.

p2a_POP_exploratory_methods: Binary: optimal=7.6923076923076925%, timeout=28/65, median attempts=2; Incremental: optimal=7.6923076923076925%, timeout=29/65, median attempts=2; Repeated: optimal=7.6923076923076925%, timeout=28/65, median attempts=2.

p2a_SAT_exploratory_methods: Binary: optimal=7.6923076923076925%, timeout=28/65, median attempts=2; Incremental: optimal=7.6923076923076925%, timeout=30/65, median attempts=2; Repeated: optimal=7.6923076923076925%, timeout=27/65, median attempts=2.

p2b_Binary_exploratory_pairs: POHP vs Gurobi_ILP, common cases=78, both proven timed=6; medians=0.1344393499311991 / 0.961106650007423 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: POHP vs CPLEX_MIP, common cases=78, both proven timed=6; medians=0.1344393499311991 / 1.0633469999884255 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: POHP vs CPLEX_CP, common cases=78, both proven timed=5; medians=0.02064469992183149 / 0.14253260020632297 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: Gurobi_ILP vs CPLEX_MIP, common cases=78, both proven timed=9; medians=4.613147799856961 / 2.3333651999710128 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: Gurobi_ILP vs CPLEX_CP, common cases=78, both proven timed=9; medians=4.613147799856961 / 0.153762900037691 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Binary_exploratory_pairs: CPLEX_MIP vs CPLEX_CP, common cases=78, both proven timed=8; medians=2.111938249960076 / 0.1492644500103779 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POHP vs Gurobi_ILP, common cases=78, both proven timed=6; medians=0.08501714999874821 / 0.7614594999831752 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POHP vs CPLEX_MIP, common cases=78, both proven timed=6; medians=0.08501714999874821 / 0.7255736999795772 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: POHP vs CPLEX_CP, common cases=78, both proven timed=5; medians=0.03556769998976961 / 0.20339829997101333 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: Gurobi_ILP vs CPLEX_MIP, common cases=78, both proven timed=9; medians=6.064277799989213 / 2.60371579999628 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: Gurobi_ILP vs CPLEX_CP, common cases=78, both proven timed=9; medians=6.064277799989213 / 0.2272324000223307 s. Pairwise samples can differ; do not combine these into a universal ordering.

p2b_Repeated_exploratory_pairs: CPLEX_MIP vs CPLEX_CP, common cases=78, both proven timed=8; medians=1.8340323999946122 / 0.22241915000631707 s. Pairwise samples can differ; do not combine these into a universal ordering.

100_or_less/david.col: largest observed runtime at k=86, status=SAT, t=0.334972s. Smaller k was slower in 31/86 adjacent observed pairs. Timeout k range: none recorded; range does not imply every interior k timed out.

- SAT: n=77, median recorded solve=0.028534s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=10, median recorded solve=0.00427605s. This is descriptive; different k and censoring preclude a significance claim.

250/anna.col: largest observed runtime at k=136, status=SAT, t=1.37158s. Smaller k was slower in 50/137 adjacent observed pairs. Timeout k range: none recorded; range does not imply every interior k timed out.

- SAT: n=128, median recorded solve=0.0600058s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=10, median recorded solve=0.0074665s. This is descriptive; different k and censoring preclude a significance claim.

500/DSJC500_1.col: largest observed runtime at k=496, status=SAT, t=33.1942s. Smaller k was slower in 226/499 adjacent observed pairs. Timeout k range: (6, 14); range does not imply every interior k timed out.

- SAT: n=486, median recorded solve=2.51544s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=5, median recorded solve=0.0225102s. This is descriptive; different k and censoring preclude a significance claim.

750/homer.col: largest observed runtime at k=558, status=SAT, t=31.1264s. Smaller k was slower in 5/8 adjacent observed pairs. Timeout k range: none recorded; range does not imply every interior k timed out.

- SAT: n=9, median recorded solve=3.01573s. This is descriptive; different k and censoring preclude a significance claim.

dense/flat300_20_0.col: largest observed runtime at k=30, status=TIMEOUT, t=34.1785s. Smaller k was slower in 127/299 adjacent observed pairs. Timeout k range: (12, 39); range does not imply every interior k timed out.

- SAT: n=261, median recorded solve=2.08805s. This is descriptive; different k and censoring preclude a significance claim.

- UNSAT: n=11, median recorded solve=0.0740125s. This is descriptive; different k and censoring preclude a significance claim.

Size, density, k and structure can all affect difficulty. Single-graph bucket samples and historical metadata gaps prevent claims about all large graphs or native solver families.
