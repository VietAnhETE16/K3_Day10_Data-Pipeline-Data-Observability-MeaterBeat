# Báo cáo vai trò cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Trần Tuấn Trung |
| MSSV | 2A202601769 |
| Khóa/Lớp | K3 |
| Tên nhóm | MeaterBeat |
| Vai trò chính | Role 3 — Corruption & Integration Owner |
| Repository | github.com/VietAnhETE16/K3_Day10_Data-Pipeline-Data-Observability-MeaterBeat |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Controlled Data Corruption | `src/ingestion/corruption.py` | `papers_clean.csv` | `papers_clean_corrupted.csv`, `corruption_log.json` | Hoàn thành |
| Phase 2 Pipeline Integration | `src/pipelines/corruption_flow.py` | `papers_clean_corrupted.csv`, `raw_records.json` | Khởi chạy end-to-end luồng đánh giá, sửa lỗi và đánh giá lại | Hoàn thành |
| State Comparison Report | `src/observability/reporting.py` (Hàm `generate_corruption_report`) | Metrics và Quality reports của 3 pha | `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động hỗ trợ | Module/thành viên nhận hỗ trợ | Kết quả |
|---|---|---|
| Tích hợp mô hình Embeddings | Role 2 — Evaluation & Observability Owner | Tích hợp thành công mô hình OpenAI `text-embedding-3-small` vào phần build index cho dữ liệu lỗi và dữ liệu sửa lỗi |
| Debug luồng khôi phục dữ liệu | Role 1 — Data Ingestion & Cleaning Owner | Xác minh logic clean chạy lại từ raw records cached hoạt động thông suốt mà không cần fetch lại Crossref |

Phạm vi sở hữu của Role 3 tập trung vào việc mô phỏng lỗi dữ liệu (Corruption), tích hợp luồng pipeline Phase 2 và viết báo cáo đối chiếu. Các phần việc trích xuất Crossref, làm sạch cơ bản (Role 1), cũng như thiết lập bộ test đóng băng và cấu hình evaluator (Role 2) là dữ liệu đầu vào và hạ nguồn được kế thừa.

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/artifact liên quan | Kết quả thực tế | Cách xác minh |
|---|---|---|---|
| Gây lỗi dữ liệu có kiểm soát | `corruption.py`, `papers_clean_corrupted.csv` | Tạo tập dữ liệu lỗi gồm 25 hàng với 4 loại lỗi | Đọc số hàng dữ liệu lỗi và kiểm tra tệp tin log |
| Nhật ký gây lỗi | `corruption_log.json` | Lưu vết chính xác 4 lỗi đụng trúng test set | Đọc tệp tin JSON nhật ký gây lỗi |
| Tích hợp luồng chạy Phase 2 | `corruption_flow.py` | Luồng chạy tự động từ dữ liệu lỗi -> đánh giá -> sửa dữ liệu -> đánh giá lại | Chạy lệnh `python script/run_corruption_flow.py` |
| Sinh báo cáo đối chiếu 3 pha | `reporting.py`, `corruption_report.md` | Xuất báo cáo markdown so sánh metrics RAG và Observability | Đọc tệp tin `corruption_report.md` trong thư mục reports |

### Output tiêu biểu

- Nhật ký lỗi: `data/results/corruption_log.json` ghi nhận 4 bản ghi bị lỗi (Blank Summary, Stale Date, Duplicate Record, và Noise Injection).
- Tập dữ liệu lỗi: `data/clean/papers_clean_corrupted.csv` chứa 25 dòng (nhiều hơn 1 dòng so với baseline do lỗi Duplicate).
- Báo cáo so sánh 3 trạng thái: `data/reports/corruption_report.md` thể hiện sự sụt giảm F1 và Judge Score từ 1.0/5.0 xuống 0.9/4.7 ở pha lỗi, và phục hồi hoàn toàn về 1.0/5.0 ở pha sửa.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Để kiểm chứng tính thiết thực của hệ thống giám sát dữ liệu (Observability) và độ nhạy của bộ chỉ số đánh giá RAG, hệ thống cần được chủ động đưa vào các kịch bản lỗi dữ liệu thực tế (Controlled Corruption). Các lỗi này phải đụng trúng (overlap) các tài liệu trong bộ câu hỏi test để phản ánh sự sụt giảm chất lượng câu trả lời của Agent. Sau đó, quy trình cần khôi phục tự động dữ liệu (Repair) từ nguồn thô đáng tin cậy để sửa chữa Vector DB và phục hồi chất lượng câu trả lời.

### Cách triển khai
*   **Controlled Data Corruption**: 
    1. Hàm `corrupt_clean_dataframe` đọc tệp test set đóng băng `test_set.json` để lấy danh sách các mã bài báo (`paper_id`) được hỏi.
    2. Thực hiện 4 kịch bản lỗi trực tiếp lên 4 bài báo này:
        - *Blank Summary*: Làm rỗng tóm tắt của bài báo đầu tiên.
        - *Stale Date*: Đổi ngày xuất bản bài báo thứ hai về năm 2000 và tính lại `age_days = 9700` để kích hoạt lỗi Freshness.
        - *Duplicate Record*: Nhân bản hàng chứa bài báo thứ ba giữ nguyên `paper_id`.
        - *Noise Injection*: Chèn một đoạn ký tự nhiễu ngẫu nhiên vào `text_for_embedding` của bài báo thứ tư.
    3. Ghi chép chi tiết các thay đổi vào `corruption_log.json`.
*   **Orchestration & Repair Pipeline**:
    1. Nạp tập dữ liệu lỗi vào ChromaDB và chạy Evaluator trên bộ test đóng băng để thu về các chỉ số pha lỗi.
    2. Chạy quy trình Repair bằng cách tải lại `crossref_records.json` sạch do Role 1 bàn giao và chạy lại hàm `build_clean_dataframe` chuẩn để tái tạo hoàn chỉnh tệp sạch gốc.
    3. Nạp lại cơ sở dữ liệu vector ChromaDB bằng dữ liệu sửa và chạy đánh giá lại để thu về chỉ số pha phục hồi.
*   **Báo cáo so sánh**: Tổng hợp kết quả JSON của 3 pha và tự động xuất bản báo cáo so sánh dưới dạng bảng Markdown 3 cột rõ ràng.

### Data contract bàn giao

*   Input: `papers_clean.csv` (dữ liệu sạch), `test_set.json` (bộ test), `crossref_records.json` (raw records gốc).
*   Output: `papers_clean_corrupted.csv` (tệp lỗi), `corruption_log.json` (nhật ký lỗi), `corruption_report.md` (báo cáo so sánh).
*   Các mô-đun phụ thuộc: `src/core/config.py`, `src/core/utils.py`, `src/retrieval/index.py`, `src/evaluation/metrics.py`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương pháp thực hiện sửa lỗi dữ liệu (Repair).
- **Các phương án đã cân nhắc:**
    1.  Viết code lọc và sửa chữa trực tiếp trên tệp lỗi `papers_clean_corrupted.csv` (ví dụ: tìm dòng trùng và xóa, tìm ngày 2000 và đổi lại ngày cũ).
    2.  Chạy lại toàn bộ data cleaning pipeline từ nguồn dữ liệu thô ban đầu `crossref_records.json` để sinh mới hoàn toàn tệp sạch.
- **Phương án đã chọn:** Phương án 2 (Chạy lại cleaning pipeline từ raw records).
- **Lý do:** Đảm bảo tính toàn vẹn (Data Integrity) và tính tái lập (Reproducibility) cao nhất. Phương án 1 khó mở rộng khi số lượng kịch bản lỗi tăng lên, dễ gây nảy sinh lỗi phụ và không tuân thủ triết lý "Source of Truth". Chạy lại từ raw records sạch ban đầu đảm bảo dữ liệu sau sửa chữa trùng khớp hoàn toàn 100% với dữ liệu sạch gốc ban đầu, tạo ra lineage rõ ràng và dễ bảo trì.
- **Bằng chứng quyết định phù hợp:** Kết quả thực nghiệm cho thấy sau khi chạy repair theo Phương án 2, toàn bộ chỉ số chất lượng của Agent và các kiểm tra Observability đều phục hồi hoàn toàn về trạng thái hoàn hảo giống hệt Baseline ban đầu.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `chromadb.errors.NotFoundError: Collection [papers-baseline] does not exist` khi chạy script sau khi server khởi động lại.
- **Nguyên nhân gốc:** Tệp manifest cấu hình `papers_embeddings.json` được lưu trữ chứa đường dẫn tuyệt đối `persist_path` cứng của máy nhà phát triển cũ (`D:\Data\doanh\...`), dẫn đến việc hàm load index cố gắng tìm kiếm cơ sở dữ liệu trên phân vùng ổ đĩa không tồn tại của máy hiện tại.
- **Cách xử lý:** Chạy lại lệnh build index trên môi trường máy hiện tại để cập nhật đúng đường dẫn tuyệt đối của máy cục bộ (`C:\Users\VIET ANH\...`) vào tệp manifest cấu hình `papers_embeddings.json`.
- **Điều học được:** Tránh lưu các đường dẫn tuyệt đối (Absolute paths) cố định trong tệp cấu hình chia sẻ. Cần ưu tiên dùng đường dẫn tương đối hoặc tự động phát hiện thư mục gốc của workspace khi nạp index.

## 7. Hiểu biết về luồng end-to-end

1.  **Dữ liệu đi từ Crossref đến vector index**: API của Crossref cung cấp dữ liệu thô (raw JSON) -> Parse thành record chuẩn -> Rerun cleaning logic (chuẩn hóa văn bản, trích xuất tác giả, tính freshness) -> Tạo văn bản embedding ghép nối -> Gửi qua API của OpenAI tạo vector -> Lưu trữ cục bộ vào ChromaDB.
2.  **Đo lường bằng Evaluation Set**: Bộ test cố định chứa các câu hỏi chuẩn kèm theo Ground Truth và mã tài liệu chứa đáp án (`ground_truth_doc_ids`).
    *   *Đo Retrieval*: So sánh tài liệu được thu hồi bởi RAG có chứa tài liệu chuẩn hay không (`retrieval_hit_rate`).
    *   *Đo Answer*: So sánh từ vựng (Token F1) và ngữ nghĩa (LLM Judge) giữa câu trả lời sinh ra từ Agent so với Ground Truth.
3.  **Quality checks vs Freshness monitoring**:
    *   *Quality checks*: Kiểm tra tính toàn vẹn tĩnh của dữ liệu tại thời điểm ghi (trùng lặp ID, rỗng trường thông tin, độ dài tối thiểu).
    *   *Freshness monitoring*: Theo dõi tính cập nhật động của dữ liệu dựa trên khoảng thời gian phát hành để cảnh báo nếu hệ thống sử dụng dữ liệu cũ quá hạn.
4.  **Dùng chung test set**: Giữ nguyên test set giúp thiết lập một hệ quy chiếu đo lường duy nhất và khách quan, cho phép so sánh định lượng chính xác sự sụt giảm chất lượng (degradation) và khả năng phục hồi (recovery) của Agent.
5.  **Đánh giá Repair thành công**: Dựa trên báo cáo chất lượng quay lại trạng thái **`PASS`** (không còn lỗi tĩnh hay stale) và các metrics chính của Agent (F1 và LLM Judge Score) phục hồi hoàn toàn về mức tối ưu ban đầu (`1.0` và `5.0`).

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.0 | 1.0 | 1.0 | Ground-truth document vẫn được tìm thấy trong top-k |
| `mean_token_f1` | 1.0 | 0.9 | 1.0 | Nội dung lỗi làm giảm độ khớp câu trả lời; repair phục hồi hoàn toàn |
| `judge_accuracy` | 1.0 | 0.9 | 1.0 | Judge phát hiện một phần answer bị ảnh hưởng bởi corruption |
| `mean_judge_score` | 5.0 | 4.7 | 5.0 | Chất lượng answer giảm rồi quay về baseline |
| Quality status | PASS | FAIL | PASS | Corrupted data vi phạm đúng các quality dimensions |
| Freshness status | PASS | FAIL | PASS | Ngày cũ giả lập được phát hiện và repair |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1.  **Lỗi dữ liệu** (Làm trống summary & làm cũ ngày xuất bản) ➔ **Observability báo `FAIL`** (completeness và freshness đều hỏng) ➔ **Agent metrics sụt giảm** (mean_token_f1 giảm về `0.9` và mean_judge_score giảm về `4.7`).
2.  **Hành động sửa lỗi** (Chạy lại logic cleaning chuẩn từ raw records) ➔ **Observability phục hồi thành `PASS`** ➔ **Agent metrics phục hồi hoàn toàn** (mean_token_f1 và mean_judge_score quay lại `1.0` và `5.0`).

*Corruption nào ảnh hưởng rõ nhất và vì sao?*
Lỗi làm trống tóm tắt (Blank Summary) và chèn nhiễu (Noise Injection) ảnh hưởng rõ ràng nhất. Vì RAG Agent hoàn toàn phụ thuộc vào nội dung ngữ cảnh thu hồi để trả lời câu hỏi factual. Việc thiếu hụt hoặc nhiễu nội dung làm suy giảm trực tiếp khả năng trích xuất đáp án chuẩn của Agent.

*Kết quả nào khác với kỳ vọng ban đầu?*
Chỉ số `retrieval_hit_rate` vẫn đạt `1.0` ở pha lỗi (Corrupted). Kỳ vọng ban đầu là khi dữ liệu lỗi, khả năng tìm kiếm sẽ giảm. Tuy nhiên, do tiêu đề của các bài báo vẫn được giữ nguyên và trường thông tin này mang trọng số ngữ nghĩa rất cao trong câu truy vấn, ChromaDB vẫn tìm thấy đúng tài liệu (HIT) mặc dù nội dung tóm tắt bên trong tài liệu đó đã bị hỏng.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1.  Việc tạo lỗi dữ liệu có chủ đích (Controlled Corruption) là phương pháp thực nghiệm tốt nhất để chứng minh giá trị của Data Observability trong một hệ thống dữ liệu.
2.  Quy trình phục hồi dữ liệu (Repair) nên được thiết kế dựa trên các "Source of Truth" sạch thay vì cố gắng chắp vá sửa lỗi trực tiếp trên tệp tin kết quả bị lỗi.
3.  Tính tương thích và di động của các tệp manifest cấu hình (như tránh lưu cứng absolute path) là rất quan trọng để đảm bảo data pipeline chạy được trên mọi máy của các thành viên.

### Hướng cải thiện

- Tự động hóa việc kiểm tra tính tương thích và phát hiện lỗi đường dẫn tuyệt đối trong các tệp manifest trước khi load index.
- Xây dựng thêm cơ chế tự động cảnh báo (Alerting) gửi email/slack khi phát hiện kiểm tra chất lượng dữ liệu báo trạng thái `FAIL`.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Báo cáo phản ánh đúng phần việc của Role 3 — Corruption & Integration Owner.
- [x] Mọi số liệu trong báo cáo đều được đối chiếu trực tiếp với các tệp tin kết quả thực tế trên đĩa.
- [x] Báo cáo này không chứa `.env`, API key, token hoặc thông tin bí mật.
- [x] Báo cáo không phải là bản sao nguyên văn từ báo cáo của các thành viên khác.

**Họ và tên:** Trần Tuấn Trung
**Ngày xác nhận:** 2026-08-06
