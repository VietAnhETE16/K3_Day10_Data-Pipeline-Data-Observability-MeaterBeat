# Báo cáo vai trò cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Lương Đăng Doanh |
| MSSV | 2A202601209 |
| Khóa/Lớp | K3 |
| Tên nhóm | MeaterBeat |
| Vai trò chính | Role 1 — Data Ingestion & Cleaning Owner |
| Repository | github.com/VietAnhETE16/K3_Day10_Data-Pipeline-Data-Observability-MeaterBeat |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Crossref ingestion | `src/ingestion/crossref.py` | Crossref Works API | `crossref_response.json`, `crossref_records.json` | Hoàn thành |
| Raw data contract | `PaperRecord`, `parse_crossref_payload`, `load_raw_records` | Crossref JSON và raw snapshot | Danh sách record phẳng, có schema ổn định | Hoàn thành |
| Cleaning và data modeling | `src/ingestion/cleaning.py` | Danh sách `PaperRecord` | `papers_clean.csv`, `papers_clean.json` | Hoàn thành |
| Lineage và artifact validation | Raw response, raw records, clean records | Các artifact đã ghi trên đĩa | Bằng chứng count, schema và truy vết theo DOI | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động hỗ trợ | Module/thành viên nhận hỗ trợ | Kết quả |
|---|---|---|
| Bàn giao clean schema và `paper_id` ổn định | Role 2 — Evaluation & Observability | Evaluation set có thể tham chiếu ngược về đúng tài liệu nguồn qua `ground_truth_doc_ids` |
| Xác minh artifact trước khi chạy baseline | Pipeline integration owner | Chứng minh raw/clean JSON đọc được, count nhất quán và không cần fetch lại Crossref khi raw snapshot đã tồn tại |
| Đối chiếu dữ liệu sau corruption/repair | Role 2 và Role 3 | Xác nhận repaired data được phục hồi từ raw records đáng tin cậy; không nhận ownership phần corruption hoặc evaluator |

Phạm vi sở hữu của Role 1 dừng tại ingestion, cleaning và dữ liệu bàn giao. Các file `testset.py`, `metrics.py`, `quality.py`, `phase1.py` và corruption flow thuộc các vai trò downstream; báo cáo này chỉ sử dụng artifact của các phần đó để chứng minh chất lượng dữ liệu Role 1 tạo ra.

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/artifact liên quan | Kết quả thực tế | Cách xác minh |
|---|---|---|---|
| Thu thập metadata từ Crossref | `crossref.py`, `data/raw/crossref_response.json` | Nhận 24 works từ đúng endpoint Crossref | Parse trực tiếp trường `message.items` trong raw response |
| Parse dữ liệu về schema phẳng | `crossref_records.json` | 24/24 record hợp lệ theo `PaperRecord` | Kiểm tra danh sách JSON và thứ tự trường schema |
| Retry và backoff | `fetch_source_records` | Retry tối đa 4 lần cho HTTP 429/503; ưu tiên `Retry-After`, nếu thiếu dùng exponential backoff | Kiểm tra nhánh status code và thời gian delay trong code |
| Làm sạch JATS/XML/HTML | `cleaning.py` | Không còn markup trong title/summary của 24 record | Quét biểu thức `<[^>]+>` trên clean JSON, kết quả 0 dòng vi phạm |
| Chuẩn hóa author/category | `authors_joined`, `categories_joined` | List được làm phẳng, loại trùng và nối bằng dấu phẩy | Đối chiếu list gốc với trường joined của toàn bộ clean records |
| Chuẩn hóa freshness | `published`, `age_days` | Ngày đúng `YYYY-MM-DD`; toàn bộ `age_days` đúng với ngày chạy | Tính lại chênh lệch ngày cho từng record |
| Tạo nội dung retrieval | `text_for_embedding` | 24/24 dòng đúng contract | So sánh lại chuỗi theo template cố định |
| Lưu clean artifacts | `papers_clean.csv`, `papers_clean.json` | Hai định dạng đều có 24 dòng và cùng schema | Đọc lại CSV/JSON từ đĩa và so sánh count/cột |

### Output tiêu biểu

- Raw HTTP body: `data/raw/crossref_response.json` — 166.143 bytes.
- Parsed records: `data/raw/crossref_records.json` — 24 records.
- Clean CSV: `data/clean/papers_clean.csv` — 24 records.
- Clean JSON: `data/clean/papers_clean.json` — 24 records.
- Lineage mẫu: DOI `10.2118/234689-pa` xuất hiện và khớp title xuyên suốt raw response → raw record → clean record → evaluation reference.

Chênh lệch raw/clean bằng 0 không phải do cleaning không hoạt động. Query Crossref đã dùng `has-abstract:true`, và batch nhận được không có record thiếu DOI/title/summary, không có summary dưới 100 ký tự và không có DOI trùng. Vì vậy cả 24 records đều vượt qua các quy tắc làm sạch.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Crossref trả metadata có cấu trúc không đồng nhất: title thường nằm trong list, abstract có thẻ JATS/XML, author là list các dict `given`/`family`, ngày xuất bản dùng `date-parts`, còn PDF URL nằm trong list link. Nếu đưa trực tiếp dữ liệu này vào retrieval, nội dung embedding sẽ chứa markup, author khó truy vấn và freshness không thể tính ổn định.

### Cách triển khai ingestion

1. Gửi request tới `https://api.crossref.org/works` với `query`, `filter` và `rows` lấy từ `Settings`.
2. Khi gặp 429 hoặc 503, retry tối đa 4 lần; đọc `Retry-After` nếu server cung cấp, nếu không dùng backoff theo lũy thừa.
3. Ghi `response.content` trực tiếp vào `crossref_response.json` để giữ raw HTTP body phục vụ audit.
4. Duyệt `message.items`, chỉ nhận record có DOI, title và abstract/description.
5. Làm phẳng author, subject, published/updated date, DOI URL và PDF URL về `PaperRecord`.
6. Ghi danh sách đã parse vào `crossref_records.json`; `load_raw_records` kiểm tra lại top-level list và schema khi đọc cache.

### Cách triển khai cleaning

1. Dùng `HTMLParser` chuẩn của Python để tách text khỏi các thẻ như `<jats:p>` và `<b>` mà không thêm dependency ngoài.
2. Chuẩn hóa whitespace; hỗ trợ cả author dạng string và nested dict.
3. Loại record thiếu `paper_id`, thiếu title sau cleaning hoặc summary dưới 100 ký tự.
4. Loại phần tử author/category trùng theo so sánh không phân biệt hoa thường; nối bằng `, `.
5. Chuẩn hóa `published` và `updated` thành `YYYY-MM-DD`; tính `age_days` theo UTC tại thời điểm chạy.
6. Deduplicate theo `paper_id`, sắp xếp ổn định và tạo:

```text
Title: [title] | Authors: [authors_joined] | Summary: [summary]
```

7. Ghi đồng thời CSV và JSON vào đúng path trong `Settings`.

### Data contract bàn giao

Clean artifact có 16 trường:

`paper_id`, `title`, `summary`, `authors`, `categories`, `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`, `comment`, `authors_joined`, `categories_joined`, `summary_chars`, `age_days`, `text_for_embedding`.

Các trường quan trọng đối với downstream:

- `paper_id`: định danh tài liệu và nối lineage/evaluation ground truth.
- `text_for_embedding`: đầu vào duy nhất để xây vector index.
- `authors_joined`, `published`, `summary`: metadata để trả lời factual question.
- `age_days`: tín hiệu freshness cho observability.

## 5. Một quyết định kỹ thuật quan trọng

### Quyết định: tách raw response và parsed records thành hai artifact độc lập

Các phương án đã cân nhắc:

1. Chỉ lưu parsed records: dung lượng nhỏ và dễ dùng, nhưng không thể audit chính xác response nguồn hoặc parse lại khi schema thay đổi.
2. Chỉ lưu response gốc: bảo toàn nguồn nhưng mọi downstream job phải hiểu cấu trúc Crossref phức tạp.
3. Lưu cả hai dạng: raw body phục vụ audit và parsed records phục vụ pipeline.

Phương án 3 được chọn. Chi phí là lưu trữ trùng một phần dữ liệu, nhưng đổi lại pipeline có lineage rõ ràng, có thể chạy lại offline từ `crossref_records.json` và không fetch ngoài ý muốn khi raw cache đã tồn tại. Đây cũng là nền tảng để repair dữ liệu corrupted từ nguồn đã đóng băng thay vì che lỗi trực tiếp trên output.

## 6. Một lỗi hoặc blocker đã xử lý

### Lỗi kết nối Crossref trong môi trường sandbox

- Triệu chứng: `requests.exceptions.ProxyError`, kết nối bị chuyển tới proxy `127.0.0.1:9` và bị từ chối.
- Nguyên nhân: môi trường chạy mặc định chặn network, không phải lỗi endpoint hoặc parser.
- Cách xử lý: chạy đúng hàm ingestion trong phiên được cấp quyền network, không thay endpoint và không lấy dữ liệu từ nguồn khác.
- Kết quả: tải thành công 24 records; cả raw response và parsed records được ghi vào đúng path.
- Kiểm tra sau xử lý: đọc lại JSON, xác minh 24 response items, 24 raw records, kích thước file khác 0 và lineage DOI đọc được.

Điều học được là log “done” không đủ chứng minh ingestion thành công. Cần mở artifact trên đĩa, parse lại, so count và kiểm tra ít nhất một lineage sample trước khi bàn giao.

## 7. Hiểu biết về luồng end-to-end

1. Crossref API cung cấp metadata thô; Role 1 lưu nguyên response và chuyển thành `PaperRecord`.
2. Cleaning biến raw records thành corpus nhất quán, loại markup và tạo `text_for_embedding`.
3. Retrieval owner dùng trường này để tạo embedding và lưu ChromaDB; metadata giữ `paper_id` để truy vết.
4. Evaluation owner dùng frozen test set gồm question, ground truth và `ground_truth_doc_ids` để đo retrieval và answer quality.
5. Observability owner kiểm tra completeness, uniqueness và freshness trên cùng clean schema.
6. Corruption owner tạo dữ liệu lỗi có chủ đích; repair phải đọc lại raw records đáng tin cậy do Role 1 bàn giao.

Frozen test set phải giữ nguyên giữa baseline, corrupted và repaired. Nếu thay câu hỏi theo từng trạng thái, chênh lệch metric có thể đến từ độ khó bộ test chứ không còn phản ánh tác động của chất lượng dữ liệu.

`retrieval_hit_rate` đo cấu phần retrieval: tỷ lệ câu hỏi có tài liệu ground-truth xuất hiện trong top-k. Chỉ số này không tự chứng minh câu trả lời cuối cùng đúng. Token F1 đo overlap từ vựng giữa answer và ground truth; khi mô hình diễn đạt lại, thêm bối cảnh, bỏ qualifier hoặc thay dấu câu, F1 có thể dưới 1 dù retriever đã tìm đúng tài liệu.

## 8. Phân tích kết quả từ artifact downstream

Các số liệu dưới đây được dùng để đánh giá tác động của dữ liệu Role 1 bàn giao; việc triển khai evaluator, quality checks và corruption không thuộc ownership của Role 1.

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.0 | 1.0 | 1.0 | Ground-truth document vẫn được tìm thấy trong top-k |
| `mean_token_f1` | 1.0 | 0.9 | 1.0 | Nội dung lỗi làm giảm độ khớp câu trả lời; repair phục hồi hoàn toàn |
| `judge_accuracy` | 1.0 | 0.9 | 1.0 | Judge phát hiện một phần answer bị ảnh hưởng bởi corruption |
| `mean_judge_score` | 5.0 | 4.7 | 5.0 | Chất lượng answer giảm rồi quay về baseline |
| Quality status | PASS | FAIL | PASS | Corrupted data vi phạm đúng các quality dimensions |
| Freshness status | PASS | FAIL | PASS | Ngày cũ giả lập được phát hiện và repair |

Baseline artifact chứng minh clean data đạt:

- 24 records, không thiếu `paper_id`, title hoặc summary.
- 0 summary dưới 100 ký tự.
- 0 DOI trùng.
- 0 record thiếu `age_days`, 0 record tương lai và 0 record stale với ngưỡng 180 ngày.
- Ngày mới nhất `2026-08-01`, cũ nhất `2026-02-12`.

Corrupted artifact có 25 dòng và báo FAIL vì có 1 summary rỗng/ngắn, 2 dòng mang DOI trùng và 1 record stale từ ngày `2000-01-01`. Sau repair từ raw records, quality và các answer metrics quay lại baseline. Chuỗi bằng chứng là:

```text
Raw records đáng tin cậy
→ clean baseline PASS
→ corruption làm quality FAIL và answer metrics giảm
→ repair lại từ raw records
→ quality PASS và metrics phục hồi
```

Việc `retrieval_hit_rate` vẫn bằng 1.0 trong trạng thái corrupted là kết quả cần diễn giải thận trọng. Bộ câu hỏi chứa title rõ ràng và hệ thống có exact-title lookup, nên đúng document vẫn có thể được đưa vào kết quả dù summary bên trong bị hỏng. Điều này cho thấy retrieval hit và answer correctness phải được đọc cùng nhau.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Raw artifact là một phần của data contract, không chỉ là file trung gian. Nó cho phép audit, tái lập và repair có căn cứ.
2. Chất lượng retrieval phụ thuộc trực tiếp vào cách chuẩn hóa text và metadata. Markup hoặc nested data không xử lý đúng sẽ đi thẳng vào embedding/index.
3. Mọi kết luận phải dựa trên artifact thực tế: cần parse file, đối chiếu count, schema, freshness và lineage thay vì chỉ nhìn terminal báo hoàn thành.

### Hướng cải thiện

- Ghi thêm timestamp, query/filter và checksum vào một ingestion manifest để audit lần fetch mà không cần suy luận từ file time.
- Dùng atomic write cho raw/clean artifacts để tránh file dở dang nếu tiến trình bị ngắt.
- Bổ sung schema validation rõ kiểu dữ liệu khi `load_raw_records`, không chỉ kiểm tra tên field.
- Thêm test cho malformed date, author thiếu `family`, description fallback và HTTP retry exhaustion.

## 10. Cam kết của thành viên

- [x] Báo cáo phản ánh đúng Role 1 — Data Ingestion & Cleaning Owner.
- [x] Không nhận ownership phần Evaluation/Observability hoặc Corruption của thành viên khác.
- [x] Mọi con số trong báo cáo đều được đối chiếu với artifact hiện có.
- [x] Không ghi “đã chạy thành công” cho phần không có bằng chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo không sao chép nguyên văn báo cáo nhóm hay báo cáo thành viên khác.

**Họ và tên:** Lương Đăng Doanh
**Ngày xác nhận:** 2026-08-06
