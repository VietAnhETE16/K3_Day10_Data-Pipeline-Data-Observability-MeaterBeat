# Kịch bản demo — RAG Data Observatory

Thời lượng đề xuất: **7 phút**  
Người trình bày Role 1: **Lương Đăng Doanh — Ingestion & Cleaning Owner**

## Chuẩn bị trước khi trình bày

Từ thư mục gốc project, chạy:

```powershell
uv run python script/run_demo.py --open
```

Nếu `uv` chưa có trong `PATH`:

```powershell
& 'C:\Users\Admin\.local\bin\uv.exe' run python script/run_demo.py --open
```

Hoặc dùng virtual environment hiện có:

```powershell
.\.venv\Scripts\python.exe script\run_demo.py --open
```

Mở thủ công `http://127.0.0.1:8080` nếu trình duyệt không tự bật.

Checklist 2 phút trước demo:

- Đảm bảo dashboard hiện trạng thái **Evidence complete**.
- Kiểm tra số liệu đầu trang: 24 raw, 24 clean, 20 evaluation questions.
- Thử ba nút Baseline, Corrupted và Repaired.
- Thử chọn một pipeline node và nút **Reveal ground truth**.
- Tắt notification và phóng trình duyệt toàn màn hình.

## 0:00–0:40 — Mở bài: vấn đề thật sự không chỉ là LLM

**Thao tác:** Đứng ở hero section.

**Lời nói:**

> “Một hệ thống RAG có thể dùng model rất mạnh nhưng vẫn trả lời sai nếu dữ liệu đầu vào thiếu, trùng hoặc quá cũ. Nhóm em xây RAG Data Observatory để trả lời ba câu hỏi: dữ liệu đến từ đâu, nó có đủ tin cậy không, và khi dữ liệu hỏng thì chất lượng câu trả lời thay đổi thế nào.”

> “Dashboard này không dùng số liệu giả. Mỗi chỉ số được đọc trực tiếp từ artifact của pipeline ngay khi trang tải.”

**Điểm nhấn trên màn hình:**

- Baseline retrieval hit rate: `100%`.
- Quality và Freshness: `PASS`.
- 24 raw works → 24 clean papers → 20 frozen questions.

## 0:40–2:00 — Visualize pipeline end-to-end

**Thao tác:** Cuộn đến **The Data Journey**, lần lượt chọn các node.

**Lời nói theo node:**

1. **Crossref API**

   > “Role 1 gọi đúng Crossref Works API theo keyword và filter abstract. Với lỗi tạm thời 429 hoặc 503, pipeline retry và backoff thay vì thất bại ngay.”

2. **Raw artifacts**

   > “Chúng em lưu hai lớp: response nguyên bản để audit và `PaperRecord` dạng phẳng để chạy lại offline. Đây là điểm bắt đầu của lineage.”

3. **Clean corpus**

   > “Cleaning bỏ JATS/HTML, làm phẳng author, chuẩn hóa ngày, tính `age_days` và tạo `text_for_embedding`. Batch này không mất record nào vì cả 24 record đều vượt quality rules.”

4. **Vector index**

   > “Clean corpus được embedding và đưa vào ChromaDB. `paper_id` tiếp tục được giữ trong metadata để truy vết.”

5. **Frozen test set**

   > “Cùng 20 câu hỏi được dùng cho baseline, corrupted và repaired. Nhờ giữ cố định bộ test, thay đổi metric đến từ dữ liệu chứ không đến từ độ khó câu hỏi.”

6. **Quality gates**

   > “Ba chốt chặn tính trực tiếp từ DataFrame là completeness, uniqueness và freshness.”

7. **Repair loop**

   > “Repair không sửa số liệu báo cáo. Nó dựng lại dữ liệu từ raw records đáng tin cậy rồi index và evaluate lại.”

## 2:00–3:10 — Baseline: mốc đối chứng sạch

**Thao tác:** Sang **Impact Lab**, chọn `Baseline`.

**Lời nói:**

> “Baseline là control group. Trên 20 câu hỏi, retrieval hit rate, Token F1 và judge accuracy đều đạt 1.0; mean judge score đạt 5.0.”

> “Ba quality gates đều PASS. Artifact cho thấy không thiếu `paper_id`, title hay summary; không có DOI trùng; không có record stale với ngưỡng 180 ngày.”

> “`retrieval_hit_rate` chỉ đo cấu phần retrieval: ground-truth document có nằm trong top-k không. Nó chưa khẳng định answer cuối cùng đúng.”

## 3:10–4:30 — Corrupted: dữ liệu hỏng, answer giảm

**Thao tác:** Bấm `Corrupted`. Chỉ vào metric cards, quality gates và incident list.

**Lời nói:**

> “Nhóm chủ động tạo bốn sự cố: blank summary, stale date, duplicate document và text noise. Corpus tăng từ 24 lên 25 dòng vì duplicate.”

> “Observability phản ánh đúng dữ liệu thật: completeness FAIL vì một summary rỗng/ngắn, uniqueness FAIL vì hai dòng có DOI trùng, freshness FAIL vì một ngày bị đổi về năm 2000.”

> “Token F1 giảm từ 1.0 xuống 0.9, judge accuracy còn 0.9 và mean judge score từ 5.0 xuống 4.7. Đây là bằng chứng định lượng rằng data quality ảnh hưởng đến answer quality.”

**Nếu giảng viên hỏi vì sao retrieval hit rate vẫn là 1.0:**

> “Các câu hỏi chứa title rất rõ và agent có exact-title lookup, nên đúng document vẫn vào top-k dù summary bên trong bị hỏng. Vì vậy phải đọc retrieval hit cùng Token F1 và judge score, không dùng một metric đơn lẻ.”

## 4:30–5:20 — Repaired: phục hồi có căn cứ

**Thao tác:** Bấm `Repaired`, so sánh chart ba trạng thái.

**Lời nói:**

> “Ở trạng thái repaired, nhóm không vá trực tiếp corrupted rows mà build lại từ raw snapshot. Quality và freshness quay lại PASS.”

> “Token F1 trở lại 1.0, judge accuracy 1.0 và mean judge score 5.0. Chuỗi nhân quả có đủ ba mắt xích: corruption → quality signal thay đổi → answer metric giảm; repair từ nguồn tin cậy → quality và metric phục hồi.”

## 5:20–6:15 — Lineage: truy một câu trả lời về nguồn

**Thao tác:** Sang **Lineage**, chỉ lần lượt bốn thẻ; sau đó chọn question và bấm **Reveal ground truth**.

**Lời nói:**

> “Đây là lineage của một DOI thật. Ta đi từ Crossref item sang `PaperRecord`, clean retrieval document, rồi đến evaluation question và ground truth.”

> “`ground_truth_doc_ids` không phải ID tạo tùy ý; nó chính là `paper_id` được giữ từ ingestion. Vì vậy một answer có thể truy ngược về đúng tài liệu nguồn.”

> “Đây cũng là lý do phải lưu cả raw response và raw records: một file phục vụ audit nguồn, file còn lại phục vụ reproducibility và repair.”

## 6:15–7:00 — Kết thúc bằng artifact và thông điệp

**Thao tác:** Sang **Artifacts**.

**Lời nói:**

> “Mọi kết luận vừa trình bày đều có file trên đĩa: raw response, raw records, clean corpus, embedding manifest, frozen test set, metrics, quality report và corruption log.”

> “Thông điệp cuối cùng của nhóm em là: một RAG đáng tin không chỉ cần tìm được tài liệu. Nó cần dữ liệu có lineage, quality gates đo từ dữ liệu thật, một evaluation set cố định và cơ chế phục hồi có căn cứ.”

> “Data you can trust. Answers you can defend.”

## Bộ câu hỏi dự phòng

### Token F1 có ý nghĩa gì và vì sao có thể dưới 1 dù retrieval đúng?

Token F1 đo overlap token giữa answer và ground truth. Retrieval đúng chỉ đảm bảo model có đúng context; answer vẫn có thể diễn đạt lại, thêm thông tin, bỏ qualifier hoặc khác dấu câu, làm precision/recall token dưới mức tuyệt đối.

### Quality check khác freshness monitoring thế nào?

Quality check bao gồm các contract tĩnh như đầy đủ field và duy nhất ID. Freshness tập trung vào thời gian: record mới nhất/cũ nhất, `age_days`, số dòng stale và ngưỡng chấp nhận.

### Vì sao raw và clean count đều bằng 24?

Crossref query đã có `has-abstract:true`; batch trả về không có record thiếu DOI/title/summary, không có summary dưới 100 ký tự và không có DOI trùng. Vì vậy không có hàng nào bị loại. Đây là kết quả của dữ liệu, không phải hard-code.

### Dashboard có hard-code số liệu không?

Không. `script/run_demo.py` đọc JSON trong `data/` khi endpoint `/api/dashboard` được gọi. Nút **Refresh artifacts** tải lại dữ liệu từ đĩa mà không cần build lại frontend.

### Vì sao dùng cùng frozen test set?

Để ba trạng thái có cùng hệ quy chiếu. Nếu câu hỏi thay đổi, không thể kết luận metric giảm do corruption hay chỉ vì bộ câu hỏi khó hơn.

### Hạn chế hiện tại là gì?

Exact-title lookup làm retrieval hit rate dễ đạt cao khi title xuất hiện nguyên văn trong câu hỏi. Bước tiếp theo nên có thêm paraphrased queries hoặc question không lộ title để đo semantic retrieval khó hơn.
