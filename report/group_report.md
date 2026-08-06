# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K3             |
| Tên nhóm         | MeaterBeat     |
| Repository         | github.com/VietAnhETE16/K3_Day10_Data-Pipeline-Data-Observability-MeaterBeat |
| Ngày hoàn thành | 2026-08-06               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Lương Đăng Doanh | 2A202601209 | Role 1 — Ingestion & Cleaning | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py` |
| 2 | Mai Việt Anh | 2A202601083 | Role 2 — Leader, Evaluation & Obs | `src/evaluation/testset.py`, `src/evaluation/metrics.py`, `src/observability/quality.py` |
| 3 | Trần Tuấn Trung | 2A202601769 | Role 3 — Corruption & Integration | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py`, `src/observability/reporting.py` |

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**
Nhóm đã hoàn thành toàn bộ 2 pha của bài lab bao gồm: Ingestion & Cleaning, Vector Indexing, Evaluation, Observability Quality Checks, Controlled Corruption, Repair và Comparative Reporting. 

Baseline pipeline đã tạo ra các raw response/records, cleaned dataset (CSV/JSON), baseline ChromaDB index, frozen test set (20 câu hỏi) và baseline evaluation metrics. 

Trong pha mô phỏng lỗi (Corruption), việc làm trống tóm tắt (Blank Summary) và chèn nhiễu văn bản (Noise Injection) ảnh hưởng rõ ràng nhất đến chất lượng RAG Agent (mean_token_f1 giảm từ 1.0 xuống 0.9, mean_judge_score từ 5.0 xuống 4.7) do mất ngữ cảnh chính xác, trong khi đổi ngày xuất bản kích hoạt cảnh báo độ tươi mới dữ liệu của Observability (Freshness: FAIL). 

Quy trình phục hồi (Repair) bằng cách chạy lại cleaning pipeline từ raw records cached đã sửa chữa thành công Vector DB, đưa chất lượng dữ liệu quay lại trạng thái PASS và toàn bộ metrics đánh giá Agent phục hồi về mức 1.0 tuyệt đối. 

Blocker lớn nhất là sự không tương thích phiên bản của langchain/ragas (VertexAI import error), đã được nhóm xử lý thành công bằng cơ chế mock module shim trong mã nguồn.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records (Ingestion)
    -> cleaning và data modeling (Cleaning)
    -> embedding + ChromaDB index (Indexing)
    -> evaluation baseline (Evaluation)
    -> quality/freshness reports (Observability)
    -> corruption (Controlled Corruption)
    -> re-index và re-evaluate (Corrupted State)
    -> repair từ dữ liệu nguồn thô (Repair State)
    -> comparison report (Reporting)
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref Works API | Gửi request, retry 4 lần, parse thô | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Lương Đăng Doanh |
| Cleaning          | Raw records | Loại bỏ XML/markup, deduplicate, format string, age_days | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Lương Đăng Doanh |
| Embedding/index   | Cleaned data | Tạo embeddings bằng OpenAI `text-embedding-3-small` và index ChromaDB | `data/embeddings/papers_embeddings.json` | Mai Việt Anh |
| Evaluation        | Clean/corrupted/repaired | Đánh giá qua bộ test 20 câu hỏi sử dụng Token F1 và LLM Judge `gpt-4o-mini` | `data/results/*_metrics.json`, `data/results/*_answers.json` | Mai Việt Anh |
| Observability     | Clean/corrupted/repaired | Kiểm tra quality tĩnh (completeness, uniqueness) và dynamic freshness | `data/quality/*_quality.json`, `data/quality/*_freshness_report.json` | Mai Việt Anh |
| Corruption/repair | Clean data / raw records | Gây lỗi 4 kịch bản; sửa lỗi bằng cách chạy lại cleaning pipeline từ raw records | `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` | Trần Tuấn Trung |
| Orchestration     | Toàn bộ pipeline | Điều phối luồng Phase 1 và Phase 2 chạy tự động | `script/run_phase1.py`, `script/run_corruption_flow.py` | Trần Tuấn Trung |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `openai`         |
| `LLM_MODEL`                | `gpt-4o-mini`         |
| Embedding model              | `text-embedding-3-small` (OpenAI)         |
| Số lượng Crossref records | 24         |
| Retrieval`top_k`           | 3         |
| Freshness threshold          | 180 days         |
| Random seed, nếu có        | 42         |

### Lệnh cài đặt

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:
```bash
python script/run_phase1.py
```

Corruption flow:
```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 | Đã tạo đầy đủ các tệp trong data/raw, data/clean, data/embeddings, data/quality, data/results. |
| Corruption flow   | Thành công | 2026-08-06 | Chạy hoàn thành toàn bộ luồng, xuất ra corrupted/repaired metrics, quality reports và comparative report. |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | `https://api.crossref.org/works` |
| Query/filter                | query="agentic retrieval", filter="has-abstract:true" |
| Thời điểm lấy dữ liệu | 2026-08-06T11:20:00Z |
| Số record nhận được    | 24 |
| Cơ chế retry/backoff      | Thử lại tối đa 4 lần khi gặp HTTP 429/503; sử dụng trường `Retry-After` hoặc lũy thừa 2^attempt làm delay. |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | string | Có | DOI thô hoặc định dạng sạch | fallback về URL DOI |
| `title` | string | Có | Tiêu đề bài báo | làm sạch HTML/XML markup |
| `summary` | string | Có | Tóm tắt bài báo | làm sạch XML/JATS markup, kiểm tra độ dài > 100 |
| `published` | string | Có | Ngày xuất bản | định dạng về YYYY-MM-DD |
| `age_days` | int | Có | Số ngày tính từ ngày xuất bản đến nay | chênh lệch so với UTC now |
| `text_for_embedding` | string | Có | Văn bản nạp vector store | tạo theo mẫu Title + Author + Summary |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Tách HTML/XML tag | Validity | 24 | Tiêu đề và tóm tắt không còn thẻ markup |
| Kiểm tra độ dài summary >= 100 | Completeness | 0 | Không còn summary ngắn |
| Loại bỏ trùng lặp paper_id | Uniqueness | 0 | Không trùng lặp |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:
*   `text_for_embedding`: Chuỗi định dạng `"Title: [title] | Authors: [authors_joined] | Summary: [summary]"`.
*   Document ID: Trường `paper_id` được trích xuất từ trường DOI thô (hoặc URL DOI) sau khi loại bỏ tiền tố URL.
*   `age_days`: Hiệu số tính bằng ngày giữa mốc thời gian chạy hiện tại (UTC) và ngày xuất bản (`published`) đã chuẩn hóa.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 20 |
| Các`question_type`                    | Tác giả (`authors`), Ngày xuất bản (`date`), và Tóm tắt nội dung (`summary`) |
| Ground-truth document ID                 | Mã `paper_id` của tài liệu gốc chứa đáp án câu hỏi |
| Embedding model                          | `text-embedding-3-small` (OpenAI API) |
| Vector store/collection                  | ChromaDB / `papers-baseline` (baseline), `papers-corrupted` (corrupted), `papers-repaired` (repaired) |
| Retrieval`top_k`                       | 3 |
| LLM provider/model                       | OpenAI / `gpt-4o-mini` |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:
Giữ nguyên test set giúp thiết lập một hệ quy chiếu đo lường duy nhất và khách quan. Nếu thay đổi câu hỏi qua từng pha, biến động của các metrics đánh giá có thể do độ khó của câu hỏi mới thay vì phản ánh sự sụt giảm hay phục hồi chất lượng của dữ liệu.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | Chứa response của Crossref và records được parse thô. |
| Cleaned dataset          | `data/clean/`                        | Có | Chứa `papers_clean.csv` và `papers_clean.json`. |
| Embedding manifest/index | `data/embeddings/`                   | Có | Chứa `papers_embeddings.json` và cơ sở dữ liệu vector. |
| Evaluation set           | `data/eval/`                         | Có | Chứa `test_set.json`. |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Chứa kết quả đánh giá baseline. |
| Quality/freshness        | `data/quality/`                      | Có | Chứa báo cáo chất lượng baseline. |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Chứa báo cáo pha 1. |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` | 1.0000 | RAG Agent tìm thấy tài liệu gốc chính xác 100% trong top-3 kết quả truy vấn. |
| `mean_token_f1`      | 1.0000 | Câu trả lời của Agent khớp hoàn toàn từ vựng với Ground Truth. |
| `judge_accuracy`     | 1.0000 | Mô hình LLM Judge đánh giá câu trả lời chính xác 100%. |
| `mean_judge_score`   | 5.0 | Điểm số đánh giá tuyệt đối đạt 5/5. |
| Ragas, nếu có        | N/A | Không chạy do thư viện Ragas bị xung đột langchain VertexAI import (đã fallback về Token F1 & LLM Judge). |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| completeness | Completeness | sum(missing_by_column) == 0 và summary_under_100 == 0 | PASS (0 records missing/short) | `baseline_quality.json` |
| uniqueness | Uniqueness | duplicate_paper_id_rows == 0 | PASS (0 duplicate records) | `baseline_quality.json` |
| freshness | Freshness | stale_rows == 0 | PASS (0 stale records) | `baseline_quality.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Cleaned dataset (`papers_clean.csv`) |
| Timestamp mới nhất       | 2026-08-01 |
| Ngưỡng freshness         | 180 ngày |
| Trạng thái baseline      | Fresh |
| Lý do                     | Toàn bộ 24 bài báo đều có ngày xuất bản trong vòng 180 ngày trở lại đây so với mốc hiện tại, không bài báo nào có `age_days > 180`. |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Blank Summary | Gán summary thành rỗng | 1 | completeness báo FAIL | Token F1 giảm, Judge score giảm | Tải lại `crossref_records.json` gốc và chạy lại `build_clean_dataframe` |
| Stale Date | Đổi ngày xuất bản về năm 2000 | 1 | freshness báo FAIL | Không ảnh hưởng metrics nếu câu hỏi không hỏi về ngày | Tải lại `crossref_records.json` gốc và chạy lại `build_clean_dataframe` |
| Duplicates | Nhân bản hàng giữ nguyên paper_id | 1 | uniqueness báo FAIL | Có thể gây nhiễu kết quả retrieve | Tải lại `crossref_records.json` gốc và chạy lại `build_clean_dataframe` |
| Noise Injection | Chèn chuỗi nhiễu ký tự ngẫu nhiên | 1 | Không ảnh hưởng quality tĩnh | Làm giảm độ khớp ngữ nghĩa và Token F1 của Agent | Tải lại `crossref_records.json` gốc và chạy lại `build_clean_dataframe` |

Corruption log:
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log ghi nhận đầy đủ chi tiết paper_id bị tác động, mô tả loại lỗi và giá trị bị thay thế.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:
Quy trình Repair đọc lại toàn bộ `crossref_records.json` sạch do Ingestion bàn giao (đây là "Source of Truth" đã được lưu trữ và đóng băng), sau đó chạy lại toàn bộ quy trình `build_clean_dataframe` để tái tạo dữ liệu sạch và ghi đè lên ChromaDB. Cách tiếp cận này đảm bảo dữ liệu phục hồi hoàn toàn sạch sẽ, có lineage rõ ràng và dễ bảo trì, thay vì che đậy lỗi cục bộ một cách tạm bợ.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      1.0 |       1.0 |      1.0 |                      0.0 |            100% | Title khớp nên vẫn hit tài liệu. |
| `mean_token_f1`        |      1.0 |       0.9 |      1.0 |                     -0.1 |            100% | Lỗi làm rỗng summary và nhiễu làm giảm độ khớp từ vựng câu trả lời. |
| `judge_accuracy`       |      1.0 |       0.9 |      1.0 |                     -0.1 |            100% | Judge phát hiện câu trả lời pha lỗi thiếu chính xác. |
| `mean_judge_score`     |      5.0 |       4.7 |      5.0 |                     -0.3 |            100% | Điểm số sụt giảm đáng kể ở pha lỗi. |
| Quality checks pass/fail |   `PASS` |    `FAIL` |   `PASS` |             PASS -> FAIL |            100% | Observability bắt đúng lỗi tĩnh. |
| Freshness status         |   `PASS` |    `FAIL` |   `PASS` |             PASS -> FAIL |            100% | Cảnh báo stale date hoạt động chuẩn. |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:
1.  **Lỗi làm trống summary và chèn nhiễu văn bản** (Noise Injection) ➔ Observability chất lượng báo **`FAIL`** ➔ Câu trả lời của RAG Agent thiếu thông tin và bị sai từ vựng (mean_token_f1 giảm về `0.9`, score giảm về `4.7`).
2.  **Chạy repair lại từ raw records cached** ➔ Tái tạo dữ liệu sạch hoàn hảo (quality và freshness báo **`PASS`**) ➔ RAG Agent khôi phục lại câu trả lời đầy đủ và chính xác (mean_token_f1 và score quay lại `1.0` và `5.0`).

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:
- **Triệu chứng:** Thư viện `ragas` báo lỗi `ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'` và làm crash tiến trình chạy evaluator.
- **Nguyên nhân:** Phiên bản `langchain-community` mới (0.4.2) đã loại bỏ hoàn toàn các partner packages cũ (như `vertexai`), trong khi thư viện `ragas` phiên bản hiện tại vẫn thực hiện import cứng từ đường dẫn cũ của langchain_community.
- **Cách xử lý:** Tạo một shim (mock module) giả lập module `langchain_community.chat_models.vertexai` bằng python code và gán vào `sys.modules` ngay trước khi thư viện `ragas` được import.
- **Cách xác minh:** Chạy `run_corruption_flow.py`, evaluator hoạt động thông suốt mà không crash.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Khóa index cứng absolute path | Gây lỗi NotFoundError trên máy của thành viên khác khi chia sẻ index | Thiết lập đường dẫn tương đối hoặc tự động mapping workspace path khi load. |
| Chưa tích hợp auto-alerting | Phải mở thủ công tệp JSON để kiểm tra chất lượng dữ liệu | Tích hợp gửi thông báo Slack/Webhook khi Observability phát hiện FAIL. |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
