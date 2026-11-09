# Benchmark analysis

- Runs: 36
- Valid colorings: 36/36
- Statuses: {'SOLVED': 36}

## Aggregate timing

| Method | Encoding | Graphs | Mean (s) | Median (s) | Min (s) | Max (s) |
|---|---:|---:|---:|---:|---:|---:|
| binary | POHP | 4 | 0.007050 | 0.006647 | 0.002039 | 0.012868 |
| binary | POP | 4 | 0.005187 | 0.005067 | 0.001928 | 0.008687 |
| binary | SAT | 4 | 0.006160 | 0.004913 | 0.002465 | 0.012348 |
| incremental | POHP | 4 | 0.006378 | 0.004164 | 0.001777 | 0.015406 |
| incremental | POP | 4 | 0.005199 | 0.004005 | 0.001631 | 0.011156 |
| incremental | SAT | 4 | 0.005195 | 0.003759 | 0.002337 | 0.010924 |
| repeated | POHP | 4 | 0.011279 | 0.007088 | 0.002709 | 0.028232 |
| repeated | POP | 4 | 0.008633 | 0.006130 | 0.002018 | 0.020254 |
| repeated | SAT | 4 | 0.008905 | 0.005935 | 0.003209 | 0.020543 |
