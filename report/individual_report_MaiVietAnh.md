# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Mai Việt Anh             |
| MSSV               | 2A202601083                     |
| Khóa/Lớp         | K3              |
| Tên nhóm         | MeaterBeat     |
| Vai trò chính    | Role 2 (Team Leader, Evaluation & Observability Owner) |
| Repository         | github.com/VietAnhETE16/K3_Day10_Data-Pipeline-Data-Observability-MeaterBeat |
| Ngày hoàn thành | 2026-08-06   |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Frozen Evaluation Set | `src/evaluation/testset.py` | `papers_clean.csv` | `test_set.json` (20 câu hỏi) | Hoàn thành |
| LLM Judge & Evaluator | `src/evaluation/metrics.py` | `test_set.json`, RAG outputs | `baseline_metrics.json`, `baseline_answers.json`, `corrupted_metrics.json`, `repaired_metrics.json` | Hoàn thành |
| Data Observability Checks | `src/observability/quality.py` | Clean/corrupted dataframes | Quality JSON reports (`baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Debug & Tích hợp Luồng Pipeline | Trần Tuấn Trung (Role 3 - Corruption Owner) | Tích hợp thành công các kịch bản lỗi của Role 3 vào pipeline chính mà không gặp sự cố crash. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Đóng băng bộ câu hỏi đánh giá | `src/evaluation/testset.py` | Tệp `test_set.json` chứa 20 câu hỏi factual | Đọc tệp `test_set.json` trong thư mục eval |
| Đánh giá chất lượng RAG | `src/evaluation/metrics.py` | Các tệp chỉ số chất lượng RAG và đáp án chi tiết qua 3 pha | Kiểm tra các tệp metrics trong thư mục results |
| Kiểm tra chất lượng dữ liệu đầu vào | `src/observability/quality.py` | Báo cáo kiểm tra chất lượng dữ liệu và độ tươi mới | Đọc các tệp json trong thư mục quality |

*Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:*
Bộ câu hỏi test đóng băng gồm 20 câu hỏi factual có đầy đủ đáp án chuẩn và Doc ID tương ứng từ dữ liệu sạch thực tế. Bộ câu hỏi này là thước đo chuẩn (ground truth) để đánh giá sự sụt giảm chất lượng của RAG Agent ở pha dữ liệu lỗi (F1 sụt giảm về 0.9, Judge Score giảm về 4.7, chất lượng dữ liệu báo FAIL) và sự phục hồi hoàn toàn ở pha dữ liệu sửa (F1 quay lại 1.0, Judge Score 5.0, chất lượng dữ liệu báo PASS).

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Hệ thống RAG cần một bộ câu hỏi đánh giá cố định (Frozen Test Set) trích xuất hoàn toàn từ dữ liệu sạch để làm tiêu chuẩn đo lường nhất quán hiệu năng qua 3 pha (Baseline, Corrupted, Repaired). Ngoài ra, hệ thống cần được giám sát liên tục ở cấp độ dữ liệu (Observability) nhằm phát hiện sớm các lỗi dữ liệu tĩnh (như trùng ID, dữ liệu quá hạn, thiếu tóm tắt) trước khi mô hình LLM tiêu thụ và sinh câu trả lời sai lệch.

### Cách triển khai
*   **Frozen Evaluation Set**: Áp dụng thuật toán chọn vị trí phân bổ đều (`_representative_indices`) trên tập dữ liệu sạch gồm 24 bài báo để lấy ra 20 bài báo tiêu biểu nhất. Bộ câu hỏi được tạo tự động với cấu trúc xoay vòng giữa 3 dạng: tác giả (Who authored...), nội dung (What is described...), và thời gian (When was... published).
*   **Structured LLM Judge**: Sử dụng mô hình `gpt-4o-mini` kết hợp cơ chế structured output để ép kiểu dữ liệu trả về theo schema của lớp `JudgeVerdict` (gồm điểm số từ 1-5, tính đúng/sai và phần lập luận chi tiết).
*   **Data Observability**: Xây dựng 3 chốt chặn kiểm tra: Completeness (kiểm tra rỗng và độ dài summary tối thiểu 100 ký tự), Uniqueness (kiểm tra trùng lặp trường paper_id) và Freshness (kiểm tra độ trễ phát hành so với ngưỡng 180 ngày).

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | DataFrame chứa dữ liệu sạch hoặc lỗi, tệp cấu hình Settings |
| Output                         | Tệp `test_set.json` (bộ test), các tệp JSON chỉ số và báo cáo chất lượng |
| Module phụ thuộc             | `src/core/config.py`, `src/core/utils.py`, `src/retrieval/index.py` |
| Module sử dụng output        | Pipeline chính (`src/pipelines/corruption_flow.py`) và báo cáo so sánh |
| Điều kiện lỗi cần xử lý | Tự động Fallback về chấm điểm heuristic bằng Token F1 nếu LLM hoặc API key gặp sự cố ngoại lệ |

### Cách xác minh

```bash
python src/evaluation/testset.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Tạo thành công bộ câu hỏi 20 câu; chạy thành công luồng đánh giá và ghi nhận điểm số sụt giảm khi dữ liệu bị lỗi, phục hồi hoàn toàn sau khi sửa.
- **Kết quả thực tế:** Tất cả các tệp JSON báo cáo chất lượng và metrics được tạo chính xác tại các thư mục quality và results.
- **Artifact/log:** Các tệp `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`, `corrupted_quality.json`, `repaired_quality.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn bộ sinh vector (Embeddings model) cho hệ thống. Starter code ban đầu chỉ định sử dụng mô hình local `sentence-transformers/all-MiniLM-L6-v2`. Tuy nhiên, môi trường local gặp vấn đề tương thích khi tải mô hình và thiếu thư viện liên quan.
- **Các phương án đã cân nhắc:**
    1.  Cố gắng sửa lỗi môi trường local để chạy được `sentence-transformers` (yêu cầu cài đặt các gói torch/transformers dung lượng lớn).
    2.  Chuyển sang tích hợp API của OpenAI với mô hình `text-embedding-3-small` thông qua gói `langchain-openai` đã sẵn có.
- **Phương án đã chọn:** Phương án 2 (Sử dụng OpenAI Embeddings).
- **Lý do:** Trade-off tối ưu về thời gian triển khai, hiệu năng và tính tái lập (reproducibility). Việc sử dụng API giúp loại bỏ hoàn toàn các phụ thuộc tính toán nặng cục bộ, rút ngắn thời gian cài đặt thư viện và đảm bảo chất lượng tìm kiếm ngữ nghĩa vượt trội với hit rate luôn đạt 1.0 tuyệt đối.
- **Bằng chứng quyết định phù hợp:** Tiến trình build index và thực hiện tìm kiếm ngữ nghĩa hoạt động thông suốt với tốc độ nhanh và cho độ chính xác cao.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'` xuất hiện khi import thư viện `ragas`.
- **Lệnh hoặc bước tái hiện:** Khởi chạy tiến trình đánh giá metrics có liên quan đến việc import Ragas.
- **Nguyên nhân gốc:** Phiên bản `langchain-community` mới (0.4.2) đã loại bỏ hoàn toàn các partner packages cũ (như `vertexai`), trong khi thư viện `ragas` phiên bản hiện tại vẫn thực hiện import cứng từ đường dẫn cũ của langchain_community.
- **Cách xử lý:** Tạo một shim (mock module) giả lập module `langchain_community.chat_models.vertexai` bằng python code và gán vào `sys.modules` ngay trước khi thư viện `ragas` được import:
  ```python
  if "langchain_community.chat_models.vertexai" not in sys.modules:
      shim = types.ModuleType("langchain_community.chat_models.vertexai")
      shim.ChatVertexAI = type("ChatVertexAI", (), {})
      sys.modules["langchain_community.chat_models.vertexai"] = shim
  ```
- **Cách xác minh sau khi sửa:** Đánh giá Ragas được tiếp tục thực thi bình thường mà không bị crash hệ thống.
- **Điều học được:** Việc hiểu sâu cơ chế import và quản lý module của Python (`sys.modules`) giúp xử lý linh hoạt các lỗi không tương thích phiên bản của thư viện bên thứ ba mà không cần can thiệp trực tiếp sửa đổi mã nguồn thư viện đó.

## 7. Hiểu biết về luồng end-to-end

1.  **Dữ liệu đi từ Crossref đến vector index**: API của Crossref cung cấp dữ liệu thô (raw JSON) -> Parse thành record chuẩn -> Rerun cleaning logic (chuẩn hóa văn bản, trích xuất tác giả, tính freshness) -> Tạo văn bản embedding ghép nối -> Gửi qua API của OpenAI tạo vector -> Lưu trữ cục bộ vào ChromaDB.
2.  **Đo lường bằng Evaluation Set**: Bộ test cố định chứa các câu hỏi chuẩn kèm theo Ground Truth và mã tài liệu chứa đáp án (`ground_truth_doc_ids`).
    *   *Đo Retrieval*: So sánh tài liệu được thu hồi bởi RAG có chứa tài liệu chuẩn hay không (`retrieval_hit_rate`).
    *   *Đo Answer*: So sánh từ vựng (Token F1) và ngữ nghĩa (LLM Judge) giữa câu trả lời sinh ra từ Agent so với Ground Truth.
3.  **Quality checks vs Freshness monitoring**:
    *   *Quality checks*: Kiểm tra tính toàn vẹn tĩnh của dữ liệu tại thời điểm ghi (trùng lặp ID, rỗng trường thông tin, độ dài tối thiểu).
    *   *Freshness monitoring*: Theo dõi tính cập nhật động của dữ liệu dựa trên khoảng thời gian phát hành để cảnh báo nếu hệ thống sử dụng dữ liệu cũ quá hạn.
4.  **Dùng chung test set**: Giữ nguyên test set giúp thiết lập một hệ quy chiếu đo lường duy nhất và khách quan, cho phép so sánh định lượng chính xác sự sụt giảm chất lượng (degradation) và khả năng phục hồi (recovery) của Agent.
5.  **Đánh giá Repair thành công**: dựa trên báo cáo chất lượng quay lại trạng thái **`PASS`** (không còn lỗi tĩnh hay stale) và các metrics chính của Agent (F1 và LLM Judge Score) phục hồi hoàn toàn về mức tối ưu ban đầu (`1.0` và `5.0`).

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      1.0 |       1.0 |      1.0 | Khả năng thu hồi tài liệu của ChromaDB luôn ổn định. |
| `mean_token_f1`      |      1.0 |       0.9 |      1.0 | F1 sụt giảm ở pha lỗi do summary rỗng và nhiễu văn bản. |
| `judge_accuracy`     |      1.0 |       0.9 |      1.0 | LLM Judge phát hiện câu trả lời pha lỗi bị thiếu thông tin. |
| `mean_judge_score`   |      5.0 |       4.7 |      5.0 | Điểm số trung bình giảm rõ rệt ở pha lỗi. |
| Quality checks         |   `PASS` |    `FAIL` |   `PASS` | Báo cáo kiểm định chất lượng phát hiện đúng lỗi dữ liệu. |
| Freshness status       |   `PASS` |    `FAIL` |   `PASS` | Cảnh báo độ tươi mới hoạt động chính xác. |

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

1.  Thiết kế một data pipeline hoàn chỉnh bắt buộc phải đi kèm với hệ thống giám sát chất lượng dữ liệu (Data Quality & Observability) để làm chốt chặn phát hiện lỗi sớm.
2.  Chất lượng dữ liệu quyết định chất lượng câu trả lời của mô hình ngôn ngữ (Garbage In - Garbage Out); RAG Agent dù thông minh đến đâu cũng không thể sinh câu trả lời đúng nếu ngữ cảnh đầu vào bị hỏng.
3.  Cơ chế kiểm thử nhất quán bằng test set đóng băng là phương pháp khoa học duy nhất để chứng minh tác động của chất lượng dữ liệu lên hệ thống AI.

### Nếu có thêm thời gian

Tích hợp thêm bộ kiểm soát ảo giác (Hallucination Guardrails) và cơ chế tự động sửa lỗi truy vấn (Query Rewriter) trong phần RAG Agent để giúp hệ thống tự động phát hiện và cảnh báo người dùng khi ngữ cảnh thu hồi từ cơ sở dữ liệu có dấu hiệu bất thường.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Mai Việt Anh
**Ngày xác nhận:** 2026-08-06
