# HƯỚNG DẪN THIẾT LẬP RAG (RETRIEVAL-AUGMENTED GENERATION)
## HỆ THỐNG WEBSITE BÁN QUẦN ÁO THÔNG MINH
**Môn học:** Niên luận Chuyên ngành Kỹ thuật Phần mềm  

---

## 1. RAG LÀ GÌ VÀ TẠI SAO BÁN QUẦN ÁO CẦN RAG?

### 1.1. Vấn đề của Chatbot thông thường (Non-RAG)
Nếu bạn chỉ kết nối một mô hình AI (như ChatGPT, Gemini) với website bán hàng mà không có RAG:
* **Hiện tượng "Ảo giác" (Hallucination):** AI sẽ tự "bịa" ra các mẫu áo, màu sắc, hoặc giá tiền mà cửa hàng của bạn không hề có.
* **Không biết tồn kho thực tế:** AI không biết hôm nay Size L áo Oxford còn bao nhiêu cái trong CSDL SQL.
* **Tư vấn size sai lệch:** Mỗi thương hiệu quần áo có bảng size (Size Chart) riêng. AI thông thường sẽ đoán bừa dẫn đến khách mua nhầm size và đổi trả hàng.

### 1.2. Cách hệ thống này truy xuất và trả lời
Ứng dụng lấy catalog và tồn kho từ SQLite, xếp hạng bằng trọng số từ vựng kiểu TF-IDF kết hợp cosine similarity, lọc theo ràng buộc truy vấn, rồi dựng câu trả lời từ dữ liệu đã kiểm chứng. Hệ thống không tạo embedding và không dùng vector database.

---

## 2. QUY TRÌNH 4 BƯỚC THIẾT LẬP RAG TRONG HỆ THỐNG

Sơ đồ quy trình thực hiện trong mã nguồn dự án:

```
┌─────────────────────────────────────────────────────────────────┐
│               BƯỚC 1: LẬP CHỈ MỤC (INDEXING / CHUNKING)          │
│  CSDL SQL (products, variants) ──► Chuyển đổi thành Documents  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              BƯỚC 2: LỌC & XẾP HẠNG TỪ VỰNG (RETRIEVAL)         │
│  Query/catalog tokens ──► IDF-style weighting + cosine (Top-K)  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│            BƯỚC 3: TĂNG CƯỜNG NGỮ CẢNH (AUGMENTATION)           │
│  System Rules + Retrieved Products ──► Augmented Prompt         │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│             BƯỚC 4: CHỌN TOOL & DỰNG CÂU TRẢ LỜI                │
│ Gemini chọn tool (tùy chọn) ──► Python kiểm chứng/render template│
└─────────────────────────────────────────────────────────────────┘
```

---

### BƯỚC 1: CHUẨN BỊ DỮ LIỆU & LẬP CHỈ MỤC (INGESTION & CHUNKING)
* **Vị trí file code:** [services/rag_engine.py](services/rag_engine.py), [services/rag_rules.py](services/rag_rules.py)
* **Cơ chế hoạt động:**
  Hệ thống truy vấn SQLite (bảng `products`, `product_variants`, `categories`). Với mỗi sản phẩm, hệ thống dựng một document trong bộ nhớ gồm thông tin sản phẩm, giá, chất liệu, bảng size, mô tả và các biến thể/tồn kho. Đây là dữ liệu runtime, không phải kho embedding/vector độc lập.

```python
# Ví dụ 1 Document được tạo ra trong hệ thống:
{
    "product_id": 1,
    "product_name": "Áo Sơ Mi Nam Oxford Slimfit Tay Dài",
    "category": "Áo Nam",
    "price": 349000,
    "content": """
        Sản phẩm: Áo Sơ Mi Nam Oxford Slimfit Tay Dài.
        Danh mục: Áo Nam.
        Giá bán: 349,000 VNĐ.
        Chất liệu: 100% Cotton Oxford dệt sợi đôi, đứng form.
        Phong cách: Công sở, Dự tiệc nhẹ, Đi phỏng vấn.
        Bảng tư vấn size: Size S: 1m55-1m64 (50-57kg) | Size M: 1m65-1m72 (58-65kg) | Size L: 1m70-1m78 (66-74kg) | Size XL: 1m75-1m85 (75-85kg).
        Tồn kho hiện tại: Trắng (Size M: 25 chiếc, Size L: 20 chiếc), Xanh Nhạt (Size M: 18 chiếc).
    """
}
```

---

### BƯỚC 2: LỌC CATALOG VÀ COSINE TRÊN TỪ VỰNG
* **Vị trí file code:** [services/rag_engine.py](services/rag_engine.py), [services/rag_rules.py](services/rag_rules.py)
* **Cơ chế hoạt động:**
  Khi người dùng nhập câu hỏi vào widget chat:
  > *"Tôi cao 1m70 nặng 64kg muốn tìm áo sơ mi đi tiệc"*

  1. **Tokenization:** Chuẩn hóa tiếng Việt, tách từ và mở rộng nhóm từ đồng nghĩa.
  2. **Trọng số và cosine:** Tính trọng số từ document/catalog theo IDF-style term weighting, sau đó cosine similarity giữa query tokens và document tokens. Đây là vector số trong bộ nhớ tạo từ từ vựng, không phải embedding do mô hình sinh:
  
$$\text{Similarity}(Q, D) = \frac{\vec{Q} \cdot \vec{D}}{\|\vec{Q}\| \|\vec{D}\|}$$

  3. **Lọc & xếp hạng:** Truy vấn có thể lọc loại/giới tính, chất liệu, ngân sách, màu, size, chiều cao/cân nặng và tồn kho trước khi lấy tối đa 3 kết quả. Ngưỡng cosine hiện dùng là 0.15 để đưa vào nhóm gợi ý; vùng 0.1 được dùng cho ứng viên cần làm rõ.

---

### BƯỚC 3: TĂNG CƯỜNG NGỮ CẢNH (PROMPT AUGMENTATION)
* **Vị trí file code:** [services/rag_engine.py](services/rag_engine.py)
* **Cơ chế hoạt động:**
  Hệ thống không gửi câu hỏi đơn độc cho AI, mà tự động xây dựng một **Augmented Prompt** (Prompt đã được nạp tài liệu trích xuất ở Bước 2):

```markdown
BẠN LÀ TRỢ LÝ TƯ VẤN THỜI TRANG AI CỦA CỬA HÀNG AURA FASHION.
QUY TẮC: Chỉ tư vấn dựa vào tài liệu trích xuất bên dưới, giải thích rõ lý do chọn size theo chiều cao cân nặng của khách.

=== DỮ LIỆU SẢN PHẨM TRÍCH XUẤT TỪ CSDL (RETRIEVED CONTEXT) ===
[Tài liệu 1]:
Sản phẩm: Áo Sơ Mi Nam Oxford Slimfit Tay Dài.
Giá: 349.000 VNĐ.
Bảng size: Size M: 1m65-1m72 (58-65kg) | Size L: 1m70-1m78 (66-74kg)...
Tồn kho: Màu Trắng (Size M: 25 chiếc)...

=== CÂU HỎI CỦA KHÁCH HÀNG ===
"Tôi cao 1m70 nặng 64kg muốn tìm áo sơ mi đi tiệc"
```

---

### BƯỚC 4: CHỌN TOOL, DỰNG CÂU TRẢ LỜI VÀ TRACE
* **Vị trí file code:** [services/rag_engine.py](services/rag_engine.py), [services/agentic_rag.py](services/agentic_rag.py)
* Khi có `GEMINI_API_KEY`, Gemini dùng function calling để chọn một tool cửa hàng (ví dụ tìm sản phẩm, tra tồn kho, tư vấn size). Tự động thực thi function của SDK bị tắt; backend kiểm tra đối số, chạy tool đọc SQLite rồi dựng câu trả lời bằng template Python từ kết quả đó. Gemini không tự sinh dữ kiện catalog cuối cùng.
* Khi không có API key hoặc Gemini lỗi, hệ thống chạy các quy tắc cục bộ và template.
* RAG Trace hiển thị `generation_mode`: `llm_router + template_render` khi Gemini chọn tool; `template` ở các luồng template/local. Trace có query tokens, kết quả/tool calls và dữ liệu hiển thị trong RAG Inspector.
* Product card được dựng từ kết quả catalog; người dùng có thể mở trang sản phẩm.

---

## 3. CÁCH KIỂM TRA VÀ BẢO VỆ ĐỒ ÁN TRƯỚC GIẢNG VIÊN

Khi thuyết trình đồ án Niên luận chuyên ngành, bạn có thể thực hiện theo kịch bản mẫu sau:

1. **Thử nghiệm tìm kiếm thông minh:**
   * Mở Chatbot ở góc phải màn hình, bấm vào gợi ý mẫu: `"👔 Áo sơ mi 1m70 65kg"`.
   * Kiểm tra bảng size trong catalog và giải thích hệ thống đối chiếu số đo với dữ liệu đó; không khẳng định mọi câu hỏi luôn có duy nhất một size đúng.
2. **Trình diễn công cụ RAG Inspector:**
   * Bấm nút **"RAG Trace"** ở góc trên khung chat.
   * Đọc `generation_mode`, query tokens, sản phẩm/tool được truy xuất, `similarity_score` nếu có và prompt/trace được trả về ở lượt đó.
3. **Trình diễn tính toàn vẹn CSDL (SQL & Triggers):**
   * Tạo checkout, dùng một thẻ/OTP mẫu được liệt kê trong README, rồi mở **"SQL & Triggers"** để xem log. Transaction và hoàn kho được xử lý bởi Python; SQLite triggers ghi nhận trạng thái đơn và biến động tồn kho.
