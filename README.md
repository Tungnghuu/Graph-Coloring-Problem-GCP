# Graph Coloring Problem

## Chạy benchmark so sánh

Tạo bảng tổng hợp Repeated SAT, Binary Search SAT và Incremental SAT trên
dataset nhỏ:

```powershell
python benchmark.py --dataset 100_or_less --limit 4 --time-limit 30
```

Kết quả tổng hợp nằm ở `results/benchmark_summary.csv`; kết quả từng lần thử
(`k`, status, thời gian encode/solve) nằm trong `results/attempts/`.

Phân tích bảng kết quả và tạo bảng speedup:

```powershell
python analyze_results.py --attempts-dir results\attempts
```

Tạo thêm biểu đồ thời gian trung bình bằng Matplotlib:

```powershell
python -m pip install matplotlib
python analyze_results.py --attempts-dir results\attempts --plot
```

Các file phân tích nằm trong `results/analysis/`: `REPORT.md`,
`timing_summary.csv`, `speedup_vs_repeated.csv` và
`mean_elapsed_time.png` nếu dùng `--plot`.

Có thể chạy ILP/CP khi máy đã cài solver tương ứng:

```powershell
python benchmark.py --methods binary --encodings Gurobi_ILP CPLEX_MIP CPLEX_CP
```

Nếu thiếu `gurobipy` hoặc `docplex`, benchmark sẽ báo package bị thiếu và
bỏ qua encoding đó; các encoding còn khả dụng vẫn tiếp tục chạy.

Gurobi Restricted License và CPLEX Community Edition cũng có giới hạn kích
thước model. Khi vượt giới hạn, benchmark ghi `ERROR` cho đúng encoding/graph
và tiếp tục các ca còn lại; không nên dùng các ca đó để so sánh thời gian.

Không push branch này lên GitHub; sau khi review có thể commit hoặc mở PR.