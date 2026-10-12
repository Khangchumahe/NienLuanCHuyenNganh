# 🛍️ AURA FASHION - WEBSITE BÁN QUẦN ÁO TÍCH HỢP RAG AI & THANH TOÁN ẢO
> **Đề tài:** Niên luận Chuyên ngành Kỹ thuật Phần mềm  
> **Ngôn ngữ & Công nghệ:** Python (Flask), SQLite3 (ACID, Triggers, Indexes, Stored Procedures), RAG Engine (Cosine Similarity Vector Search), HTML5 / Vanilla CSS / JavaScript ES6.

---

## 📖 MỤC LỤC
1. [Giới Thiệu Đề Tài](#1-giới-thiệu-đề-tài)
2. [Cấu Trúc Thư Mục](#2-cấu-trúc-thư-mục)
3. [Hướng Dẫn Cài Đặt & Chạy Local](#3-hướng-dẫn-cài-đặt--chạy-local)
4. [Các Tính Năng Trọng Tâm & Cách Sử Dụng](#4-các-tính-năng-trọng-tâm--cách-sử-dụng)
5. [Quy Trình Làm Việc Nhóm Qua Git & GitHub](#5-quy-trình-làm-việc-nhóm-qua-git--github)
6. [Kịch Bản Demo Báo Cáo Cho Giảng Viên](#6-kịch-bản-demo-báo-cáo-cho-giảng-viên)

---

## 1. GIỚI THIỆU ĐỀ TÀI
Hệ thống là một nền tảng thương mại điện tử chuyên ngành thời trang với 3 trụ cột kỹ thuật:
1. **Chatbot AI sử dụng RAG (Retrieval-Augmented Generation):** Tư vấn chọn size chuẩn xác theo chiều cao, cân nặng, phong cách dựa trên dữ liệu sản phẩm thực tế trong kho (không bị ảo giác/hallucination).
2. **Cổng thanh toán ảo mô phỏng (Virtual Sandbox Payment):** Mô phỏng luồng thanh toán VNPAY/MoMo với mã giao dịch, kiểm tra chữ ký điện tử HMAC-SHA256 và cơ chế Webhook IPN.
3. **Cơ sở dữ liệu quan hệ (SQL) tối ưu:** Áp dụng CRUD, Index B-Tree, Trigger tự động kiểm tra số lượng tồn kho và ghi log kiểm toán, Stored Procedure (Transaction ACID) đảm bảo trừ kho và đặt hàng an toàn tuyệt đối.

---

## 2. CẤU TRÚC THƯ MỤC
```text
NienLuanChuyenNganh/
├── database/
│   ├── schema.sql           # File DDL tạo bảng, Index và Triggers
│   ├── db.py                # Kết nối SQLite, Seed data mẫu, Stored Procedure (Transaction)
│   └── store.db             # File cơ sở dữ liệu SQLite (tự sinh khi chạy app)
├── services/
│   ├── rag_engine.py        # Pipeline RAG: Chunking, Cosine Similarity, Augmented Prompt, Trace
│   └── payment_service.py   # Dịch vụ thanh toán ảo Sandbox và tạo chữ ký số HMAC-SHA256
├── static/
│   ├── css/
│   │   └── style.css        # Giao diện hiện đại (Deep Slate, Vibrant Indigo, Glassmorphism)
│   └── js/
│       └── app.js           # Xử lý giỏ hàng, đặt hàng, Chatbot RAG và bộ RAG Inspector
├── templates/
│   └── index.html           # Giao diện chính người dùng (Client Storefront)
├── app.py                   # Máy chủ Flask Backend (RESTful API & Webhooks)
├── requirements.txt         # Danh sách thư viện Python cần thiết
├── .gitignore               # Tệp loại trừ file tạm thời khi push lên Git
├── PHAN_TICH_YEU_CAU_HE_THONG.md # Tài liệu SRS phân tích yêu cầu nghiệp vụ, chức năng & phi chức năng
├── HUONG_DAN_THIET_LAP_RAG.md    # Tài liệu giải thích chi tiết cơ chế RAG 4 bước
└── README.md                # Tài liệu hướng dẫn sử dụng và cộng tác dự án
```

---

## 3. HƯỚNG DẪN CÀI ĐẶT & CHẠY LOCAL

### Yêu cầu hệ thống:
* Đã cài đặt **Python 3.10** hoặc mới hơn (khuyên dùng Python 3.11).
* Đã cài đặt **Git**.

### Các bước thực hiện:

#### Bước 1: Clone dự án về máy tính
Mở Terminal / PowerShell và gõ:
```bash
git clone <URL_REPO_GITHUB_CUA_NHOM>
cd NienLuanChuyenNganh
```

#### Bước 2: Tạo môi trường ảo (Khuyến nghị)
* **Trên Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```
* **Trên macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Bước 3: Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

#### Bước 4: Khởi chạy máy chủ
```bash
python app.py
```

Khi chạy thành công, màn hình sẽ hiển thị:
```text
============================================================
🚀 ĐANG KHỞI CHẠY HỆ THỐNG CỬA HÀNG THỜI TRANG TÍCH HỢP RAG AI
🔗 Địa chỉ truy cập: http://127.0.0.1:5000
============================================================
```

Mở trình duyệt bất kỳ (Chrome, Edge, Firefox) và truy cập: **`http://127.0.0.1:5000`**

---

## 4. CÁC TÍNH NĂNG TRỌNG TÂM & CÁCH SỬ DỤNG

### 🛒 4.1. Mua Hàng & Chọn Biến Thể Sản Phẩm
1. Duyệt danh mục: Bấm vào các thẻ tab *Áo Nam, Quần Nam, Áo Khoác, Đầm & Váy Nữ*.
2. Bấm **"Xem chi tiết"** vào sản phẩm bất kỳ để mở cửa sổ chi tiết.
3. Chọn màu sắc và kích cỡ (Size S, M, L, XL). Hệ thống sẽ hiển thị tồn kho realtime cho từng biến thể SKU.
4. Bấm **"Thêm vào giỏ hàng"**.

### 💳 4.2. Đặt Hàng & Cổng Thanh Toán ZaloPay Sandbox Gateway (Chính Thức)
1. Bấm nút **"Giỏ hàng"** ở góc phải thanh Menu.
2. Kiểm tra danh sách mặt hàng, điền thông tin người nhận (Tên, SĐT, Địa chỉ).
3. Bấm **"Tiến Hành Thanh Toán Ảo (Virtual Sandbox)"**.
4. Cửa sổ **ZaloPay Sandbox Gateway** hiện ra theo chuẩn giao thức nhà phát hành ZaloPay & SDK `zalopay.js`:
   * **Thông tin kỹ thuật:** Mã đơn hàng, AppID (`2553`), AppTransID (`yyMMdd_xxxxxx`), Chữ ký số MAC HMAC-SHA256 chuẩn ZaloPay v2, đồng hồ đếm ngược 15:00.
   * **Kênh 1 - Thẻ Quốc Tế (Visa / Mastercard / JCB):**
     * Tích hợp sẵn danh sách **Thẻ tín dụng mẫu hoạt động được**:
       * *Visa Platinum:* `4111 1111 1111 1111` | EXP: `12/28` | CVV: `123` (Thành công)
       * *Mastercard World:* `5555 5555 5555 5555` | EXP: `10/27` | CVV: `456` (Thành công)
       * *JCB Ultimate:* `3528 0000 0000 0000` | EXP: `08/29` | CVV: `789` (Thành công)
       * *Thẻ Demo lỗi:* `4000 0000 0000 0002` (Mô phỏng từ chối do không đủ số dư để test Rollback kho).
     * Chỉ cần **1-Click** vào thẻ mẫu là hệ thống tự động điền form.
     * Bấm "Thanh toán an toàn" -> Chuyển sang bước xác thực **3D-Secure OTP** (Mã OTP mẫu: `111111`).
   * **Kênh 2 - Thẻ ATM Nội Địa Napas:**
     * Thẻ Napas ngân hàng NCB test: `9704 1985 2619 1432 198` (OTP: `123456`).
     * Thẻ Napas ngân hàng Vietcombank test: `9704 3666 1234 5678`.
   * **Kênh 3 - Ví ZaloPay QR:**
     * Quét mã QR hoặc nhập tài khoản ví test `0912345678` (OTP: `111111`).
   * **Xử lý toàn vẹn dữ liệu:**
     * Khi hoàn tất thanh toán thành công: Kích hoạt Stored Procedure `sp_ProcessPaymentWebhook` chuyển trạng thái đơn hàng sang `PAID`, kích hoạt Trigger trừ kho & ghi log kiểm toán.
     * Khi bấm **"Hủy giao dịch"**: Tự động kích hoạt cơ chế hoàn lại tồn kho đã giữ chỗ trong kho dữ liệu (Rollback Trigger).

### 🤖 4.3. Chatbot Trợ Lý Thời Trang RAG
1. Bấm vào nút nổi tròn **"Tư Vấn Chọn Size (RAG AI)"** ở góc dưới bên phải màn hình.
2. Bạn có thể bấm vào các câu hỏi gợi ý nhanh hoặc tự nhập câu hỏi, ví dụ:
   * *"Tôi cao 1m70 nặng 65kg muốn tìm áo sơ mi đi làm"*
   * *"Gợi ý áo khoác chống nước đi phượt"*
   * *"Tìm đầm lụa dự tiệc cưới thanh lịch che khuyết điểm"*
3. Chatbot sẽ tra cứu kho và trả về lời khuyên kèm theo các **thẻ sản phẩm** trực tiếp. Bấm vào thẻ sản phẩm để xem ngay thông tin.

### 🔍 4.4. Công Cụ RAG Inspector (Minh Chứng Kỹ Thuật)
* Ở đầu cửa sổ Chatbot, bấm nút **"RAG Trace"**.
* Hệ thống sẽ hiển thị modal phân tích toàn diện 3 bước của RAG:
  1. **Query Tokens:** Từ khóa bóc tách từ câu hỏi của bạn.
  2. **Cosine Retrieval:** Danh sách tài liệu sản phẩm lấy từ CSDL SQL và điểm tương đồng (`similarity_score`).
  3. **Augmented Prompt:** Toàn bộ nội dung prompt được tiêm ngữ cảnh gửi cho AI.

### ⚡ 4.5. Kiểm Tra CSDL SQL & Triggers (SQL Audit)
* Trên thanh menu chính, bấm nút **"SQL & Triggers"**.
* Modal sẽ hiển thị tổng số sản phẩm, biến thể, đơn hàng và bảng nhật ký kích hoạt thực tế của Trigger `trg_track_order_status` và `trg_log_inventory_change`.

---

## 5. QUY TRÌNH LÀM VIỆC NHÓM QUA GIT & GITHUB

Để 3 thành viên trong nhóm làm việc nhịp nhàng, không bị đè code lên nhau (conflict), hãy tuân thủ quy trình sau:

### 👥 Phân chia nhánh (Branching Strategy):
* **Nhánh chính (`main`):** Chỉ chứa code đã test kỹ, chạy ổn định (dùng để báo cáo và thuyết trình).
* **Thành viên 1 (Frontend & UI):** Làm việc trên nhánh `feature/frontend-ui`
* **Thành viên 2 (Backend & Database SQL):** Làm việc trên nhánh `feature/backend-sql`
* **Thành viên 3 (AI RAG & Payment):** Làm việc trên nhánh `feature/ai-rag-payment`

### 💻 Quy trình làm việc hàng ngày:

#### 1. Lấy code mới nhất từ nhánh `main` về:
```bash
git checkout main
git pull origin main
```

#### 2. Tạo hoặc chuyển sang nhánh chức năng của mình:
```bash
# Ví dụ thành viên 1 làm frontend:
git checkout -b feature/frontend-ui
# Nếu nhánh đã có từ trước:
git checkout feature/frontend-ui
```

#### 3. Sau khi chỉnh sửa code, commit và đẩy lên GitHub:
```bash
git add .
git commit -m "feat(ui): chỉnh sửa giao diện chi tiết sản phẩm và bảng size"
git push -u origin feature/frontend-ui
```

#### 4. Tạo Pull Request (PR) trên GitHub:
* Lên trang web GitHub của Repository.
* Bấm **"Compare & pull request"**.
* Gắn thẻ 2 thành viên còn lại để review code trước khi gộp (Merge) vào nhánh `main`.

---

## 6. KỊCH BẢN DEMO BÁO CÁO CHO GIẢNG VIÊN

Khi lên báo cáo môn Niên luận chuyên ngành, nhóm nên thực hiện theo thứ tự 3 bước sau:

1. **Bước 1 (Trình diễn Nghiệp vụ Bán hàng & Triggers SQL):**
   * Mở web, chọn sản phẩm, chọn size/màu.
   * Đặt hàng và thực hiện thanh toán ảo thành công.
   * Mở modal **"SQL & Triggers"** để giảng viên thấy Trigger CSDL tự động ghi log trạng thái và xuất kho.
2. **Bước 2 (Trình diễn Chatbot RAG AI):**
   * Nhập câu hỏi tư vấn chiều cao cân nặng vào Chatbot AI.
   * Cho thầy/cô thấy bot tư vấn chính xác size áo dựa vào dữ liệu thực tế của shop.
3. **Bước 3 (Minh chứng Kỹ thuật RAG với RAG Inspector):**
   * Bấm **"RAG Trace"** trên khung chat để giải thích công thức Cosine Similarity và cách Augmented Prompt hoạt động.

---
*Chúc nhóm hoàn thành xuất sắc đồ án Niên luận chuyên ngành Kỹ thuật Phần mềm!* 🎓
