# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** DDGPT
**Thành viên:** 
Trần Nguyễn Thái Duy 
Đinh Mạnh Dũng 
Nguyễn Hồng Phi 
Phạm Thành Trung 
Từ Hoàng Giang
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ & Quy định Thư viện Đại học (University Library Services & Regulations — University of Toronto Scarborough / UTSC)

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề dịch vụ và quy định thư viện đại học nhằm đáp ứng đúng yêu cầu của lớp K4-L3A về quy định/dịch vụ học vụ. Dịch vụ thư viện có các quy định rõ ràng về hạn mượn, chính sách thiết bị, không gian học tập và có sự phân định ranh giới đối tượng sử dụng rõ rệt giữa sinh viên (`student`), giảng viên/nghiên cứu viên (`faculty`) và toàn trường (`all`). Sự phân tầng này tạo điều kiện thực tế lý tưởng để thử nghiệm và chứng minh tính hiệu quả của cơ chế `metadata_filter` cũng như các chiến lược chia đoạn (chunking).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | UTSC Library borrowing policy | https://utsc.library.utoronto.ca/borrowing | 2026-09-19 / 2025-12-17 | 5,858 | `audience: student`, `department: library`, `category: borrowing`, `language: en` |
| 2 | Course reserves and short-term loans | https://utsc.library.utoronto.ca/course-reserves-short-term-loan | 2026-09-19 / not-stated | 1,566 | `audience: student`, `department: library`, `category: course-reserves`, `language: en` |
| 3 | Technology loans | https://utsc.library.utoronto.ca/technology-loans | 2026-09-19 / not-stated | 2,855 | `audience: student`, `department: library`, `category: technology`, `language: en` |
| 4 | Services for persons with disabilities | https://utsc.library.utoronto.ca/services-persons-disabilities | 2026-09-19 / not-stated | 2,556 | `audience: all`, `department: library`, `category: accessibility`, `language: en` |
| 5 | Ask a Librarian chat service | https://utsc.library.utoronto.ca/ask-librarian-chat | 2026-09-19 / not-stated | 967 | `audience: all`, `department: library`, `category: reference-help`, `language: en` |
| 6 | Library spaces and services | https://utsc.library.utoronto.ca/library-spaces | 2026-09-19 / not-stated | 2,143 | `audience: all`, `department: library`, `category: facilities`, `language: en` |
| 7 | UTSC Library hours | https://utsc.library.utoronto.ca/hours | 2026-09-19 / 2026-09-08 | 962 | `audience: all`, `department: library`, `category: hours`, `language: en` |
| 8 | Research and publishing services for faculty | https://utsc.library.utoronto.ca/research-publishing | 2026-09-19 / not-stated | 2,610 | `audience: faculty`, `department: library`, `category: research-support`, `language: en` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `utsc-borrowing-policy` | Định danh duy nhất của tài liệu; gắn vào mọi chunk để liên kết với tài liệu gốc và hỗ trợ `delete_document(doc_id)`. |
| `title` | string | `UTSC Library borrowing policy` | Tiêu đề tài liệu, phục vụ trích dẫn và hiển thị ngữ cảnh nguồn trong câu trả lời của agent. |
| `source_url` | string | `https://utsc.library.utoronto.ca/borrowing` | Nguồn gốc minh bạch (provenance), cho phép người dùng kiểm chứng tài liệu gốc. |
| `retrieved_at` | string | `2026-09-19` | Ngày thu thập dữ liệu (định dạng `YYYY-MM-DD`), hỗ trợ kiểm soát tính cập nhật của tài liệu. |
| `document_version` | string | `2025-12-17` / `not-stated` | Phiên bản hoặc ngày hiệu lực văn bản, giúp quản trị vòng đời và phân biệt bản cũ/mới. |
| `audience` | string | `student`, `faculty`, `all` | Đối tượng áp dụng; trường cốt lõi cho `metadata_filter={"audience": "student"}` để loại bỏ tài liệu sai đối tượng trước khi tính vector similarity. |
| `department` | string | `library` | Phân loại đơn vị quản lý, hỗ trợ lọc theo phòng ban khi hệ thống mở rộng nhiều đơn vị trong trường. |
| `category` | string | `borrowing`, `technology`, `hours` | Phân loại nghiệp vụ/dịch vụ cụ thể để thu hẹp không gian tìm kiếm theo chức năng. |
| `language` | string | `en` | Ngôn ngữ văn bản, phục vụ phân tách ngôn ngữ khi corpus đa ngữ. |
| `license_or_permission` | string | `public-source` | Xác định cơ sở pháp lý và điều khoản sử dụng dữ liệu công khai theo chuẩn quản trị. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu tiêu biểu (`chunk_size=200`):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `utsc-borrowing-policy.md` (5,858 ký tự) | FixedSizeChunker (`fixed_size`) | 39 | 198.9 | Kém: Cắt ngang bảng tra cứu hạn mượn và ranh giới điều khoản phạt. |
| | SentenceChunker (`by_sentences`) | 14 | 416.6 | Khá: Giữ trọn vẹn từng câu nhưng các dòng bảng markdown bị gom cụt lủn. |
| | RecursiveChunker (`recursive`) | 41 | 141.4 | Tốt: Tách tự nhiên theo đoạn `\n\n` rồi đến dòng `\n`, các điều khoản giữ được tính độc lập. |
| `utsc-course-reserves.md` (1,566 ký tự) | FixedSizeChunker (`fixed_size`) | 11 | 187.8 | Kém: Cắt đứt các bước hướng dẫn truy cập Quercus ở giữa câu. |
| | SentenceChunker (`by_sentences`) | 6 | 259.2 | Khá: Giữ câu nguyên vẹn nhưng mất liên kết giữa tiêu đề mục và nội dung con. |
| | RecursiveChunker (`recursive`) | 10 | 155.2 | Rất tốt: Phân tách rõ ràng giữa phần giới thiệu và danh sách các bước thực hiện. |
| `utsc-technology-loans.md` (2,855 ký tự) | FixedSizeChunker (`fixed_size`) | 19 | 197.6 | Kém: Xé đôi thông số kỹ thuật của thiết bị và thời hạn cho mượn. |
| | SentenceChunker (`by_sentences`) | 14 | 202.6 | Trung bình: Gặp khó với các danh sách gạch đầu dòng ngắn (bullet points). |
| | RecursiveChunker (`recursive`) | 19 | 149.1 | Tốt: Bảo toàn cấu trúc từng nhóm thiết bị (Computing, Audio, Power). |

### Chiến lược của từng thành viên

**Thành viên 1 — Đinh Mạnh Dũng**
- **Loại chiến lược:** Recursive (`RecursiveChunker`, chunk_size=400)
- **Mô tả & lý do chọn cho chủ đề này:** Phân tách phân cấp theo danh sách separator `["\n\n", "\n", ". ", " ", ""]` kết hợp gom cụm mảnh nhỏ liền kề. Phù hợp cho văn bản quy định học vụ vì giữ trọn cấu trúc đoạn văn, hạn chế tối đa việc tạo chunk vụn hoặc cắt ngang giữa chừng.
- **Cấu hình & Kết quả:** Sinh ra 64 chunks trên corpus UTSC Library; kết hợp với `search_with_filter` (pre-filtering) để giải quyết xung đột tài liệu giữa sinh viên và giảng viên.
- **Code snippet:**
```python
from src.chunking import RecursiveChunker
chunker = RecursiveChunker(chunk_size=400)
```

**Thành viên 2 — Phạm Thanh Trung**
- **Loại chiến lược:** Heading/structural + Recursive fallback.
- **Cấu hình đã kiểm thử:** Tách tài liệu tại heading Markdown cấp 1–3 (`#`, `##`, `###`), giữ heading cùng nội dung; section dài hơn 700 ký tự được chia tiếp bằng `RecursiveChunker`; truy xuất `top_k=3`.
- **Mô tả & lý do chọn:** Tài liệu dịch vụ thư viện UTSC được tổ chức thành các mục rõ ràng như Loan privileges, Physical course reserves và TSpace. Tách theo heading giúp mỗi chunk giữ đúng chủ đề và dễ truy vết về mục gốc. Recursive fallback xử lý section quá dài mà vẫn ưu tiên ranh giới đoạn, dòng, câu và từ, hạn chế cắt giữa một quy định.
- **Metadata filter:** Dùng `category=opening-hours` cho câu giờ mở cửa, `audience=student` cho câu borrowing và course reserves, `category=technology-lending` cho câu trả laptop, và `audience=faculty` cho câu TSpace.
- **Code snippet (custom):**
```python
class HeadingChunker:
    def __init__(self, chunk_size: int = 700) -> None:
        self.chunk_size = chunk_size
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        sections = re.split(r"(?=^#{1,3}\s)", text, flags=re.MULTILINE)
        chunks = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if len(section) <= self.chunk_size:
                chunks.append(section)
            else:
                heading_match = re.match(r"^(#{1,3}\s[^\n]+)\n+", section)
                heading = heading_match.group(1) if heading_match else ""
                body = section[heading_match.end():] if heading_match else section
                for piece in self.fallback.chunk(body):
                    chunks.append(f"{heading}\n\n{piece}".strip())
        return chunks
```
- **Kết quả kiểm thử:** Đạt retrieval top-3 **5/5** và agent answer **5/5**, với tổng cộng 25 chunks.

**Thành viên 3 — Từ Hoàng Giang**
- **Loại chiến lược:** Custom Parent-child
- **Cấu hình dự kiến:** Dùng chunk con khoảng 200–300 ký tự để tìm kiếm và section cha khoảng 500–800 ký tự để đưa vào ngữ cảnh trả lời.
- **Mô tả & lý do chọn:** Chunk con nhỏ giúp tăng độ chính xác truy xuất, còn chunk cha giữ đủ nội dung của mục dịch vụ hoặc quy định. Cấu hình này dùng để kiểm tra liệu việc mở rộng ngữ cảnh có khắc phục trường hợp retrieval tìm đúng chi tiết nhưng agent thiếu thông tin xung quanh hay không.
- **Code snippet (custom):** *(Sẽ bổ sung sau khi triển khai và kiểm thử)*

**Thành viên 4 — Trần Nguyễn Thái Duy**
- **Loại chiến lược:** Heading/structural + Recursive fallback (`HeadingSectionChunker`).
- **Cấu hình đã kiểm thử:** Tách tài liệu tại các heading Markdown cấp 1–3 (`#`, `##`, `###`), giữ nguyên vẹn tiêu đề cùng nội dung của từng section; các section dài hơn ngưỡng cho phép (`chunk_size=500` ký tự) được chia tiếp bằng `RecursiveChunker` và tự động gắn lại tiêu đề mục (heading) vào từng mảnh con để bảo toàn ngữ cảnh; truy xuất `top_k=3`.
- **Mô tả & lý do chọn:** Tài liệu dịch vụ và quy định Thư viện UTSC (University of Toronto Scarborough) được biên soạn theo cấu trúc phân cấp điều khoản rõ ràng như Loan Privileges by Patron Type, Course Reserves, Return Procedures, TSpace Research Repository. Việc tách theo heading đảm bảo mỗi chunk là một đơn vị thông tin hoàn chỉnh, độc lập và dễ dàng truy vết về mục gốc (Source Traceability). Cơ chế Recursive fallback với kỹ thuật Heading Re-attachment ngăn ngừa việc làm đứt gãy bảng biểu hoặc mất đi tiêu đề của điều khoản khi gặp các mục có độ dài lớn.
- **Metadata filter:** Áp dụng `metadata_filter={"category": "hours"}` cho câu hỏi thời gian mở cửa thư viện, `metadata_filter={"audience": "student"}` cho câu hỏi hạn mức mượn tài liệu và vị trí kệ sách Course Reserves, `metadata_filter={"category": "technology"}` cho câu hỏi quy trình hoàn trả laptop mượn, và `metadata_filter={"audience": "faculty"}` cho câu hỏi kho lưu trữ nghiên cứu TSpace.
- **Code snippet (custom):**
```python
class HeadingSectionChunker:
    """Chia nhỏ theo tiêu đề Markdown (#, ##, ###) và gắn lại tiêu đề cho mảnh con."""
    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self.recursive_chunker = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        pattern = r"(?m)(?=^#{1,4}\s+)"
        sections = [s.strip() for s in re.split(pattern, text) if s.strip()]
        chunks = []
        for sec in sections:
            if len(sec) <= self.max_chunk_size:
                chunks.append(sec)
            else:
                lines = sec.split("\n", 1)
                heading = lines[0].strip() if lines[0].startswith("#") else ""
                body = lines[1] if len(lines) > 1 else ""
                sub_chunks = self.recursive_chunker.chunk(body) if body else self.recursive_chunker.chunk(sec)
                for sub in sub_chunks:
                    chunks.append(f"{heading}\n{sub}" if heading and not sub.startswith(heading) else sub)
        return chunks
```
- **Kết quả kiểm thử:** Toàn bộ corpus được chuẩn hóa dưới dạng Markdown với hệ thống đề mục chuẩn chỉnh, hoàn toàn ăn khớp với cây quyết định kiến trúc dữ liệu (Data Strategy Decision Tree) trong bài giảng. Kết quả kiểm thử trên 5 benchmark query khi kết hợp cơ chế Pre-filtering metadata đạt tỷ lệ retrieval top-3 **5/5** và agent answer **5/5**, tạo ra bộ tri thức chuẩn hóa gồm 84 chunks với độ dài trung bình 229.3 ký tự.

**Thành viên 5 — Nguyễn Hồng Phi**
- **Loại chiến lược:** *(Đang cập nhật)*
- **Cấu hình dự kiến:** *(Đang cập nhật)*
- **Mô tả & lý do chọn:** *(Đang cập nhật)*
- **Code snippet:** *(Đang cập nhật)*

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|---|---|---|---|---|
| Đinh Mạnh Dũng | RecursiveChunker (chunk_size=400) | 3 / 10 | Phân đoạn cân đối, tự nhiên theo đoạn/câu, tổng 64 chunks, giữ nguyên điều khoản học vụ. | Bị ảnh hưởng khi dùng MockEmbedder (không mã hóa ngữ nghĩa); cần kết hợp metadata filter để lọt top-3. |
| Phạm Thanh Trung | HeadingChunker + Recursive fallback (chunk_size=700) | 10 / 10 (5/5 queries) | Bảo toàn hoàn hảo ranh giới cấu trúc Markdown, chỉ 25 chunks cô đọng, giữ heading ở mọi chunk con, retrieval và agent answer đều đạt 5/5. | Phụ thuộc vào chất lượng heading của Markdown gốc; nếu tài liệu không có heading chuẩn sẽ suy biến về fallback. |
| Từ Hoàng Giang | Custom Parent-child (Child: 200–300, Parent: 500–800) | Đang thử nghiệm | Tối ưu hóa kép: vector search chính xác trên chunk con, LLM đọc ngữ cảnh đầy đủ từ chunk cha. | Độ phức tạp triển khai cao hơn, cần quản lý quan hệ mapping giữa chunk cha và con trong vector store. |
| Trần Nguyễn Thái Duy | HeadingSectionChunker + Recursive fallback (chunk_size=500) | 10 / 10 (5/5 queries) | Chia theo heading kết hợp Heading Re-attachment tự động, 84 chunks, độ dài trung bình 229.3 ký tự, retrieval top-3 5/5 và agent answer 5/5. | Sinh ra số lượng chunk nhiều hơn (84 chunks) so với cắt thô do ngưỡng 500 ký tự. |
| Nguyễn Hồng Phi | *(Chờ cập nhật)* | - | *(Chờ bổ sung)* | *(Chờ bổ sung)* |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **Chiến lược được ưu tiên theo bài giảng:** Heading/structural kết hợp Recursive fallback (được kiểm chứng qua `HeadingChunker` của Phạm Thanh Trung và `HeadingSectionChunker` của Trần Nguyễn Thái Duy).
> 
> **Lý do:**
> 1. **Phù hợp với cây quyết định bài giảng:** Corpus được lưu dưới dạng Markdown và có hệ thống heading rõ ràng (`#`, `##`, `###`), nên chiến lược cấu trúc theo heading hoàn toàn ăn khớp với cây quyết định kiến trúc dữ liệu (Data Strategy Decision Tree) trong bài giảng — vượt trội hơn hẳn cách cắt cơ học thuần túy theo số ký tự vốn xé đôi các bảng phí phạt và mốc thời gian.
> 2. **Hiệu suất thực tế kiểm chứng:** Cả hai thành viên áp dụng hướng tiếp cận này đều đạt điểm tuyệt đối **5/5 top-3 retrieval** và **5/5 agent answer** trên toàn bộ 5 benchmark queries khi kết hợp cơ chế Pre-filtering metadata.
> 3. **Bảo tồn ngữ cảnh vượt trội:** Việc gắn lại heading (Heading Re-attachment) vào đầu mỗi sub-chunk khi section quá dài giúp các mảnh con không bao giờ bị trôi mất ngữ cảnh của điều khoản quy định.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng về dạng hỏi, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Query | Gold answer | Tài liệu / vị trí chứa bằng chứng | Ghi chú đánh giá |
|---|---|---|---|---|
| 1 | What are the UTSC Library’s regular opening hours from Monday to Friday between September 8 and December 22, 2026? | The library’s regular weekday hours are 8:00 AM to 10:00 PM. It is closed on October 12, 2026. | `utsc-library-hours` — “Library Hours” | Tra cứu thời gian và nhận biết ngoại lệ. |
| 2 | As an undergraduate student, how long can I borrow regular library items, and what is my item limit? | Undergraduate students have a regular loan period of 14 days and an item limit of 50. | `utsc-borrowing-policy` — “Loan privileges by patron type at most University of Toronto Libraries” | Phân biệt quy định dành cho sinh viên đại học với các nhóm khác. |
| 3 | Where should a user return a borrowed laptop from the Technology Loans collection? | A borrowed laptop should be returned directly to the Info Desk. | `utsc-technology-loans` — đoạn mở đầu “Technology Loans”, hướng dẫn trả thiết bị | Tra cứu địa điểm và quy trình trả thiết bị. |
| 4 | A student needs to find a physical course reading placed on reserve. Where is it located? | Physical course reserves are located 20 steps to the left of the InfoDesk at the UTSC Library. | `utsc-course-reserves` — “Where are physical course reserves located?” | **A/B test:** không lọc so với `metadata_filter={"audience": "student"}`. |
| 5 | Which service provides a free and secure University of Toronto repository for disseminating and preserving faculty and graduate-student research? | TSpace – University of Toronto Research Repository. | `utsc-research-publishing` — “TSpace - University of Toronto Research Repository” | Định danh dịch vụ theo chức năng. |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Giờ mở cửa thường nhật từ T2-T6 | HeadingChunker (với filter `category=hours` hoặc `opening-hours`) | Có (Top-1) với HeadingChunker | Tách đúng section Library Hours; filter category giúp loại bỏ hoàn toàn tài liệu nhiễu. |
| 2 | Hạn mượn & định mức sinh viên đại học | HeadingChunker / RecursiveChunker (với `audience=student`) | Có (Top-1, Top-2, Top-3) | Tìm đúng bảng hạn mức mượn trong `utsc-borrowing-policy`. Đạt 2/2 điểm ở cả 2 chiến lược. |
| 3 | Nơi trả laptop mượn | HeadingChunker (với `category=technology`) | Có (Top-1) với HeadingChunker | Giữ trọn section Technology Loans - Laptop Returns và filter category giúp trả lời chính xác Info Desk. |
| 4 | Vị trí tài liệu dự trữ môn học (Course Reserves) | HeadingChunker / RecursiveChunker (có `audience=student` filter) | Có (Top-1 với HeadingChunker, Top-3 với Recursive) | Minh chứng A/B test: Filter `audience=student` loại trừ hoàn toàn tài liệu faculty, đưa đúng đoạn 20 steps to the left of InfoDesk. |
| 5 | Nền tảng lưu trữ TSpace cho nghiên cứu | HeadingChunker (với `audience=faculty`) | Có (Top-1) với HeadingChunker | Tách đúng section TSpace và filter `audience=faculty` đưa tài liệu vào top-1. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Rất hữu ích, đặc biệt rõ rệt ở Câu hỏi 4 (A/B Test):**
> - **Khi KHÔNG lọc (`metadata_filter=None`)**: Top-3 bị chiếm lĩnh hoàn toàn bởi tài liệu dành cho giảng viên (`utsc-research-publishing#5` với điểm tương đồng +0.4163) do chứa nhiều từ khóa học thuật tương tự, khiến tài liệu mục tiêu `utsc-course-reserves` bị đẩy văng khỏi top-3.
> - **Khi CÓ lọc (`metadata_filter={"audience": "student"}`)**: Hệ thống loại bỏ ngay từ đầu các tài liệu của faculty, giải phóng vị trí ứng viên và đưa đoạn văn bản mục tiêu từ `utsc-course-reserves#3` vào thẳng Top-3. Điều này chứng minh cơ chế tiền lọc (pre-filtering) là thiết yếu để bảo vệ độ chính xác khi kho tri thức có nhiều tài liệu cùng chủ đề nhưng khác đối tượng phục vụ.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Phân tích lỗi (Failure Analysis)

Nhóm phân tích 2 trường hợp lỗi tiêu biểu trong quá trình thử nghiệm benchmark:

1. **Trường hợp 1 — Câu hỏi 3 (Nơi trả laptop mượn):**
   - **Hiện tượng lỗi**: Top-1 trả về `utsc-borrowing-policy#11` (hướng dẫn trả sách tại Info Desk) thay vì trúng đoạn quy định riêng về trả laptop trong `utsc-technology-loans`.
   - **Nguyên nhân**: Cả hai tài liệu đều chứa từ khóa "return" và "Info Desk". MockEmbedder (băm MD5) đo sự trùng hợp từ ngữ ngẫu nhiên nên chunk quy định mượn trả chung có điểm tương đồng (+0.3033) cao hơn chunk của laptop.
   - **Đề xuất sửa**: (1) Bổ sung tiền lọc `category: technology` để khu biệt tài liệu thiết bị; (2) Sử dụng `HeadingChunker` để mỗi chunk luôn mang tiền tố `## Technology Loans - Laptop Returns`, giúp embedding phân biệt rõ ràng quy trình trả thiết bị với trả sách; (3) Nâng cấp lên mô hình embedding ngữ nghĩa thực.

2. **Trường hợp 2 — Câu hỏi 4 (A/B Test khi không dùng filter):**
   - **Hiện tượng lỗi**: Khi không áp dụng filter, Top-1 bị chiếm bởi tài liệu `utsc-research-publishing#5` (score +0.4163) của đối tượng `faculty`, đẩy tài liệu mục tiêu `utsc-course-reserves` văng khỏi Top-3.
   - **Nguyên nhân**: Đánh đổi giữa Precision và Recall khi không gian vector embedding bị nhiễu bởi các tài liệu học thuật cùng trường từ vựng.
   - **Đề xuất sửa**: Bắt buộc áp dụng cơ chế tiền lọc `metadata_filter={"audience": "student"}` cho các truy vấn của người học để triệt tiêu tài liệu gây nhiễu trước khi tính similarity.

### Những phân tích (insights) hay nhất nhóm sẽ trình bày:
> 1. **Hiệu ứng tiền lọc Metadata (Pre-filtering)**: Thử nghiệm A/B trên câu hỏi 4 chứng minh rằng không có filter thì tài liệu sai đối tượng sẽ nuốt trọn top-k; pre-filtering là cứu cánh duy nhất khi không gian ngữ nghĩa giữa các đối tượng bị chồng lấn.
> 2. **Ranh giới ngữ nghĩa vs Ranh giới ký tự**: `RecursiveChunker` và `HeadingChunker` vượt trội hơn `FixedSizeChunker` trong việc bảo tồn tính toàn vẹn của các bảng quy định và điều khoản học vụ.
> 3. **Giới hạn của MockEmbedder**: Mock embedding chỉ giúp kiểm thử pipeline hoạt động; điểm số bị nhiễu và đòi hỏi phải nâng cấp lên Transformer embedding để hệ thống RAG đi vào thực tế.

### Bài học rút ra khi so sánh trong nhóm:
> Cùng một tập dữ liệu và cùng một câu truy vấn, việc chọn chiến lược chunking quyết định trực tiếp việc đoạn thông tin có bị xé lẻ hay không. `FixedSizeChunker` có thể cắt đôi một dòng trong bảng mượn sách khiến mô hình không thể ghép nối được đối tượng và số ngày mượn, trong khi `RecursiveChunker` giữ trọn vẹn ngữ cảnh của bảng đó.

### Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?
> Nhóm sẽ chuẩn hóa các bảng biểu Markdown thành định dạng cặp khóa-giá trị (Key-Value) ngắn gọn hoặc danh sách có cấu trúc trước khi chunk, đồng thời bổ sung thêm các metadata chi tiết hơn như `service_type` hoặc `sub_category` để bộ lọc có thể thu hẹp phạm vi chính xác hơn nữa.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
