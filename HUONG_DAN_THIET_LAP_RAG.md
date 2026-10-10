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

### 1.2. Giải pháp RAG (Retrieval-Augmented Generation)
RAG giải quyết triệt để vấn đề này bằng nguyên lý:
> **"Trước khi trả lời (Generation), hãy tra cứu kho dữ liệu thực tế (Retrieval) rồi mới đưa vào ngữ cảnh (Augmentation) để AI đọc và trả lời."**

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
│              BƯỚC 2: VECTOR HÓA & TRÍCH XUẤT (RETRIEVAL)        │
│  User Query: "1m70 65kg sơ mi" ──► Cosine Similarity (Top-K)    │
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
│             BƯỚC 4: SINH CÂU TRẢ LỜI (GENERATION)               │
│  LLM Engine ──► Trả về câu tư vấn chính xác + Link sản phẩm     │
└─────────────────────────────────────────────────────────────────┘
```

---

### BƯỚC 1: CHUẨN BỊ DỮ LIỆU & LẬP CHỈ MỤC (INGESTION & CHUNKING)
* **Vị trí file code:** [rag_engine.py](file:///d:/NienLuanChuyenNganh/services/rag_engine.py#L20-L45)
* **Cơ chế hoạt động:**
  Hệ thống truy vấn cơ sở dữ liệu SQL (bảng `products` liên kết với `product_variants` và `categories`). Với mỗi sản phẩm, hệ thống đóng gói các trường nghiệp vụ quan trọng thành một **Tài liệu tri thức (Knowledge Document)**:

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

### BƯỚC 2: TRÍCH XUẤT TƯƠNG ĐỒNG NGỮ NGHĨA (SEMANTIC RETRIEVAL)
* **Vị trí file code:** [rag_engine.py](file:///d:/NienLuanChuyenNganh/services/rag_engine.py#L47-L105)
* **Cơ chế hoạt động:**
  Khi người dùng nhập câu hỏi vào widget chat:
  > *"Tôi cao 1m70 nặng 64kg muốn tìm áo sơ mi đi tiệc"*

  1. **Tokenization:** Bóc tách các từ khóa ngữ nghĩa: `['1m70', '64kg', 'muốn', 'tìm', 'áo', 'sơ', 'mi', 'đi', 'tiệc']`.
  2. **Vector Space Calculation:** Tính toán độ tương quan (Cosine Similarity) giữa vector câu hỏi và từng Document trong kho dữ liệu thời trang:
  
$$\text{Similarity}(Q, D) = \frac{\vec{Q} \cdot \vec{D}}{\|\vec{Q}\| \|\vec{D}\|}$$

  3. **Ranking & Filtering:** Lọc ra Top-K sản phẩm có điểm tương đồng cao nhất. Ví dụ sản phẩm *Áo Sơ Mi Oxford* đạt điểm số tương quan cao vượt trội vì khớp cả từ khóa loại áo lẫn khoảng chiều cao 1m65-1m72 (58-65kg).

---

### BƯỚC 3: TĂNG CƯỜNG NGỮ CẢNH (PROMPT AUGMENTATION)
* **Vị trí file code:** [rag_engine.py](file:///d:/NienLuanChuyenNganh/services/rag_engine.py#L107-L135)
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

### BƯỚC 4: SINH CÂU TRẢ LỜI & TRUY VẾT MINH CHỨNG (GENERATION & TRACE)
* **Vị trí file code:** [rag_engine.py](file:///d:/NienLuanChuyenNganh/services/rag_engine.py#L137-L200)
* **Cơ chế hoạt động:**
  Mô hình ngôn ngữ nhận prompt trên và sinh ra câu trả lời thuyết phục:
  > *"Dạ chào bạn! Với chiều cao 1m70 và cân nặng 64kg, bạn mặc **Size M** mẫu **Áo Sơ Mi Nam Oxford Slimfit Tay Dài** sẽ vừa vặn và tôn dáng nhất..."*

  Đồng thời, hệ thống trả về kèm:
  * **Thẻ sản phẩm tương tác (Product Card):** Khách có thể bấm vào xem chi tiết hoặc thêm giỏ ngay trong khung chat.
  * **RAG Trace Payload:** Phục vụ công cụ **RAG Inspector** trên giao diện Web để giảng viên có thể xem trực tiếp từng giai đoạn của thuật toán.

---

## 3. CÁCH KIỂM TRA VÀ BẢO VỆ ĐỒ ÁN TRƯỚC GIẢNG VIÊN

Khi thuyết trình đồ án Niên luận chuyên ngành, bạn có thể thực hiện theo kịch bản mẫu sau:

1. **Thử nghiệm tìm kiếm thông minh:**
   * Mở Chatbot ở góc phải màn hình, bấm vào gợi ý mẫu: `"👔 Áo sơ mi 1m70 65kg"`.
   * Cho thầy/cô thấy bot trả lời chính xác size M theo đúng số đo trong CSDL SQL mà không hề bịa đặt.
2. **Trình diễn công cụ RAG Inspector:**
   * Bấm nút **"RAG Trace"** ở góc trên khung chat.
   * Màn hình sẽ hiện toàn bộ 3 bước:
     * Bước 1: Từ khóa bóc tách (`1m70`, `65kg`, `áo`, `sơ`, `mi`).
     * Bước 2: Danh sách tài liệu lấy từ SQL và điểm số tương đồng `similarity_score`.
     * Bước 3: Toàn bộ nội dung Prompt đã ghép ngữ cảnh.
3. **Trình diễn tính toàn vẹn CSDL (SQL & Triggers):**
   * Mua hàng và bấm "Thanh toán thành công" ở Cổng thanh toán ảo.
   * Bấm nút **"SQL & Triggers"** trên thanh menu để mở bảng kiểm tra. Thầy cô sẽ thấy Trigger `trg_track_order_status` và `trg_log_inventory_change` tự động ghi nhận nhật ký vào bảng kiểm toán.
