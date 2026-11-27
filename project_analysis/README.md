# Phân tích thực nghiệm GCP

Pipeline bao gồm tiền xử lý, coverage/configuration, phần 1 (encoding), 2A
(search), 2B (backend), phần 3 (k-sweep), membership. Thư mục này chỉ giữ các script tạo hình và bảng.

## Chạy và kiểm chứng

Từ thư mục gốc:

```sh
python -m pip install -r requirements.txt
python -m project_analysis.run_all --exploratory
```

Có thể đặt `MPLCONFIGDIR=/tmp/gcp-mpl XDG_CACHE_HOME=/tmp/gcp-cache` khi HOME
không ghi được.

```sh
python project_analysis/run_all.py \
  --source results --data data --output project_analysis \
  --part1-method Repeated --sat-encoding POHP --exploratory
```

`--source` có thể lặp. `--output` là gốc chứa `processed/` và `outputs/`.
Không đọc các thư mục validation/reviewed tự động. Pipeline không chạy benchmark.
Các script 01–06 vẫn chạy riêng được với vị trí mặc định.

## Quy tắc dữ liệu

- CSV tìm sắc số được gom theo file run, graph identity gồm bucket/path, method,
  encoding, solver, configuration. CSV k-sweep được tách riêng.
- Run manifest `.meta.json` v2 lưu run ID, thời điểm UTC, môi trường, phiên bản,
  giới hạn, tham số, fingerprint mã nguồn, cận và lý do kết thúc.
- Cấu hình chỉ được đánh dấu verified khi có manifest v2 đủ trường. So sánh chính
  giữ cùng môi trường, implementation, giới hạn, symmetry setting và cận đầu;
  phần 1/2A còn giữ cùng SAT solver. Không lấy môi trường máy hiện tại gán cho CSV cũ.
- Các run cùng cấu hình bị lặp được giữ trong inventory nhưng loại khỏi xếp hạng
  vì chưa có quy ước ghép lần lặp. Không chọn lần nhanh nhất hay cộng các lần chạy.
- UB lấy từ SAT đã validate hoặc incumbent có số màu và validation rõ ràng.
  LB lấy từ initial/final certified bound và UNSAT+1; fallback 1 cho graph không rỗng.
  Optimal chỉ khi UB=LB; cận mâu thuẫn không dùng để so sánh. Không lấy k tại dòng
  timeout làm incumbent từ một cờ validation có thể thuộc nghiệm trước.
- `Completed`: kết thúc search có manifest, hoặc legacy có bằng chứng tối ưu.
  `Partial`: có attempt nhưng không biết kết thúc/không kết luận.
  `Timeout`: có timeout quan sát được; vẫn có thể feasible/optimal.
  `Missing`: header-only hoặc ca vắng trong expected manifest.
  `Error`: lỗi được ghi, không đọc được hoặc không có attempt hợp lệ.
  Các trạng thái completion là loại trừ nhau; proof độc lập với completion.
- Không suy ra toàn bộ thí nghiệm dự kiến từ tích Descartes. `--expected` CSV
  gồm graph_id, graph, group, method, encoding (có thể thêm backend/config_id)
  giúp đếm các run hoàn toàn vắng. Không có expected manifest thì coverage chỉ
  mô tả những file đã tìm thấy, không phải toàn bộ ca lẽ ra phải chạy.
- Metric thiếu giữ trống; không đổi thành 0. Thiếu kích thước công thức không
  làm mất bằng chứng nghiệm. Ghép đủ metric trước khi so sánh metric đó.

## Thời gian và ngân sách

`encoding_time`: tạo công thức/ràng buộc bổ sung.
`setup_time`: với SAT, khởi tạo solver/nạp công thức; Incremental tính cả append.
`solving_time`: với SAT, lời gọi solve (bao gồm quản lý timer); native là backend
call, chưa tách hết overhead nội bộ nên setup để trống, không giả định bằng 0.
`recorded_time`: tổng các thành phần đã ghi ở từng attempt, trống nếu thiếu dòng/giá trị.
`total_time`: v2 dùng wall-clock đoạn search + chi phí bounds đo trước; legacy
chỉ dùng recorded components và có `time_basis` phân biệt.

Wall-clock v2 bắt đầu sau khi tạo metadata/header, kết thúc sau đóng solver và
release encoding, trước ghi manifest cuối. Không bao gồm đọc graph, thu thập
môi trường hay ghi manifest cuối; bao gồm log attempt và decode/validation.
Cận được tính chung trước các encoding và phân bổ một lần cho mỗi run.
Ngân sách toàn run áp dụng cho search, không bao gồm cận tính trước. Giới hạn
encoding/solve là từng attempt. Hủy solver dựa trên khả năng backend; setup hay
native cleanup có thể khiến wall-clock vượt ngân sách. Đây không phải hard
process-kill deadline.

`bounds_time` chỉ lấy dòng đầu; nếu dòng sau lặp giá trị dương, gắn lỗi và loại
run khỏi so sánh thời gian. Attempts khác solver calls: encoding timeout chưa
phải một lần gọi solver. Legacy không có cờ thì calls để trống.

## Các phép so sánh

- Phần 1 mặc định Repeated, cố định solver/config; hai chart variables/clauses
  ghép cùng graph và first k. Đường theo n là median tại mỗi n; k giữa các graph
  vẫn có thể khác, không phải đường độ phức tạp chỉ phụ thuộc n.
- Phần 2A tách từng encoding, median attempts và calls riêng; chất lượng nghiệm
  được xuất từng graph. Median số màu không phải thước đo thắng thua giữa graph.
- Phần 2B chọn POHP trước khi xem kết quả, tách Repeated/Binary, có tập chung
  bốn backend và giao từng cặp. Không đòi sáu cấu hình mới cho phép so sánh một cặp.
- Runtime hoàn thành so sánh trên giao các run proven optimal có metric.
  Counts/outcomes giữ cả timeout và feasible. Scatter attempts–time thể hiện
  thời gian quan sát và đánh dấu timeout, không coi đó là time-to-solution.
- Performance profile dùng proven optimal làm thành công; run không thành công
  tương đương tỉ số vô hạn. Mẫu số gồm mọi ca ghép, kể cả tất cả backend thất bại.
- Gap=(UB-LB)/UB cho feasible chưa tối ưu, gồm cả không timeout. Thiếu cận để trống.
- Mặc định (hoặc `--exploratory`) phân tích dữ liệu lịch sử với nhãn rõ; chưa xác minh giới hạn,
  môi trường, phiên bản và POP nên không dùng làm kết luận so sánh có kiểm soát.
- Phần 3 có marker trạng thái từng graph, bảng vùng k, peak, SAT/UNSAT median,
  biểu đồ chung và coverage Missing. Một graph mỗi bucket chỉ là khảo sát ban đầu.

## POP và dữ liệu lịch sử

POP mới dùng y[v,c] = (color(v)>c), core clauses (12a–d) và symmetry bound (13)
trong [Faber et al., SAT 2024](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2024.12).
Đây là biến thể core POP với vertex-index symmetry, không tuyên bố tái lập toàn
bộ POP-S cùng mọi symmetry của bài báo. Decode/forbid-color hoạt động trực tiếp
trên biến thứ tự. 
CSV POP cũ không được đổi nhãn thành kết quả của implementation mới. Danh sách
`rerun_needed.csv` nêu các run cần xác minh/chạy lại. Không thể khôi phục setup,
wall-clock, bounds hoặc lý do dừng chính xác nếu log cũ không ghi.

## Đầu ra và truy vết

`processed/`: attempts, summary_runs, k_sweep, inventory, coverage,
configurations, data_quality, rerun_needed, comparison_membership.

`outputs/tables/`: CSV và LaTeX cho mọi bảng, bao gồm membership theo từng phép
so sánh. `outputs/figures/`: PNG/PDF. Bảng LaTeX tổng hợp cho báo cáo
(`output/tables/table1–3`) được tạo bằng `python -m project_analysis.export_latex_tables`.

Xem `VERIFICATION.md` để đối chiếu kế hoạch với test. Các kết quả trước lần sửa
được giữ riêng; chỉ các đầu ra của pipeline mới có các quy ước ở tài liệu này.

## Chế độ mặc định và biểu đồ không đủ dữ liệu

`python -m project_analysis.run_all` dùng dữ liệu hiện có, gắn nhãn exploratory
cho các so sánh chưa xác minh cấu hình. Không tự suy đoán metadata hay hạ điều
kiện chứng minh tối ưu để làm đầy biểu đồ. Dùng `--verified-only` nếu muốn chỉ
so sánh các run có metadata đã xác minh.

Không xuất ảnh thông báo trắng hoặc trục không có dữ liệu. Xem
`outputs/figure_status.csv` để biết biểu đồ nào được tạo/bỏ qua và lý do. Mỗi lần
chạy xóa hình và bảng cũ trong `outputs/` trước khi tạo lại.
Dữ liệu CSV gốc không bị thay đổi.
