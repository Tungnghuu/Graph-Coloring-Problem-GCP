# Graph Coloring Problem

## Chạy benchmark so sánh

Tạo bảng tổng hợp Repeated SAT, Binary Search SAT và Incremental SAT trên
dataset nhỏ:

```powershell
python benchmark.py --dataset 100_or_less --limit 4 --time-limit 30
```

Kết quả tổng hợp nằm ở `results/benchmark_summary.csv`; kết quả từng lần thử
(`k`, status, thời gian encode/solve) nằm trong `results/attempts/`.

Có thể chạy ILP/CP khi máy đã cài solver tương ứng:

```powershell
python benchmark.py --methods binary --encodings Gurobi_ILP CPLEX_MIP CPLEX_CP
```

Không push branch này lên GitHub; sau khi review có thể commit hoặc mở PR.