# 🛍️ AURA FASHION - WEBSITE BÁN QUẦN ÁO TÍCH HỢP RAG AI & THANH TOÁN ẢO
> **Đề tài:** Niên luận Chuyên ngành Kỹ thuật Phần mềm  
> **Ngôn ngữ & Công nghệ:** Python (Flask), SQLite, Python transaction helpers và SQLite triggers, RAG truy xuất từ vựng có trọng số TF-IDF-style kết hợp cosine similarity, HTML5 / CSS / JavaScript.

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
2. **Cổng thanh toán mô phỏng:** Giao diện và payload theo giao thức ZaloPay Sandbox; ứng dụng không gọi API thanh toán bên ngoài. Backend kiểm tra chữ ký callback, dữ liệu thẻ/OTP mẫu, xử lý idempotent và hoàn tồn kho khi giao dịch thất bại.
3. **Cơ sở dữ liệu quan hệ:** SQLite với transaction do các hàm Python điều khiển (`BEGIN IMMEDIATE`/rollback), index và SQLite triggers. Đây không phải stored procedures của MySQL/PostgreSQL.

---

## 2. CẤU TRÚC THƯ MỤC
```text
NienLuan_origin/
├── database/
│   ├── schema.sql           # Schema SQLite, index và triggers
│   ├── db.py                # ensure_schema, seed data, CRUD và transaction helpers
│   └── store.db             # DB SQLite hiện được Git theo dõi
├── services/
│   ├── rag_engine.py        # Lexical TF-IDF-style weighting, cosine, bộ lọc và trace
│   ├── agentic_rag.py       # Gemini function calling và template fallback
│   ├── rag_rules.py         # Quy tắc query/catalog dùng chung
│   ├── payment_service.py   # Payment simulator, chữ ký và thẻ/OTP mẫu
│   └── size_chart.py        # Tư vấn size
├── admin_*.py               # Route admin dùng session/RBAC hiện có
├── customer_portal.py       # Trang và API customer
├── customer_migrate.py      # Tạo bảng liên kết đơn hàng customer
├── seed_accounts.py         # CLI tạo tài khoản demo từ biến môi trường
├── config/store_policies.json # Cấu hình chính sách cửa hàng
├── docs/                    # Ghi chú rà soát
├── tests/                   # Pytest và frontend smoke test
├── static/
│   ├── css/                 # Giao diện
│   ├── img/                 # Ảnh placeholder
│   └── js/                  # app.js và stylist-chat.js
├── templates/               # Storefront, customer, product detail và chat
├── Zalopaysandbox/          # JavaScript giao diện sandbox
├── app.py                   # Máy chủ Flask Backend (RESTful API & Webhooks)
├── pytest.ini               # pytest chỉ thu thập tests/
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

### Cấu hình biến môi trường

Ứng dụng và `seed_accounts.py` nạp `.env` bằng `python-dotenv`. Không commit `.env`; các giá trị dưới đây chỉ là ví dụ giả.

| Biến | Bắt buộc? | Ví dụ giả / hành vi |
|---|---|---|
| `APP_ENV` | Nên đặt rõ | `development`; chỉ giá trị này cho phép khóa tạm sinh riêng trong tiến trình. |
| `SECRET_KEY` | Có ngoài development | `REPLACE_WITH_RANDOM_SECRET`; dùng cho session và callback checksum. Nếu thiếu ngoài development, app báo lỗi; trong development sinh khóa tạm và log cảnh báo. |
| `FLASK_SECRET_KEY` | Không | `REPLACE_WITH_ANOTHER_RANDOM_SECRET`; fallback cho Flask session nếu `SECRET_KEY` chưa đặt, nhưng không thay thế khóa mà payment service yêu cầu ngoài development. |
| `ZALOPAY_KEY1`, `ZALOPAY_KEY2` | Có ngoài development | `FAKE_ZP_KEY1`, `FAKE_ZP_KEY2`; khóa tạm trong development nếu bỏ trống. |
| `ZALOPAY_APP_ID` | Không | `1234` (giả); mặc định trong code là 2553 ở development và 0 ngoài development. |
| `FLASK_DEBUG` | Không | `0`; chỉ chuỗi `1` bật debug. |
| `FLASK_COOKIE_SECURE` | Không | `0`; đặt `1` khi chạy qua HTTPS. |
| `AURA_DB_PATH` | Không | `C:\\tmp\\aura-demo.db`; mặc định là `database/store.db`. |
| `GEMINI_API_KEY` | Không | `FAKE_GEMINI_KEY`; thiếu key thì dùng template cục bộ. |
| `GEMINI_MODEL` | Không | `gemini-2.5-flash` (mặc định hiện tại). |
| `MOMO_PARTNER_CODE`, `MOMO_ACCESS_KEY`, `MOMO_SECRET_KEY` | Không / chưa dùng trong luồng đang chạy | Ví dụ giả `FAKE_MOMO_PARTNER`, `FAKE_MOMO_ACCESS`, `FAKE_MOMO_SECRET`; code chỉ khai báo cấu hình, không gọi API MoMo. |
| `AURA_SUPPORT_PHONE` | Không | `0900000000` (số minh họa). |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME`, `ADMIN_PHONE` | Không; cần email+mật khẩu nếu muốn seed ADMIN | `admin@example.test`; tự đặt mật khẩu mạnh, tối thiểu 8 ký tự. |
| `STAFF_EMAIL`, `STAFF_PASSWORD`, `STAFF_NAME`, `STAFF_PHONE` | Không; cần email+mật khẩu nếu muốn seed STAFF | `staff@example.test`; ví dụ giả. STAFF hiện không có quyền admin. |
| `CUSTOMER_EMAIL`, `CUSTOMER_PASSWORD`, `CUSTOMER_NAME`, `CUSTOMER_PHONE` | Không; cần email+mật khẩu nếu muốn seed CUSTOMER | `customer@example.test`; ví dụ giả. |

### Tạo tài khoản demo

Sao chép `.env.example` thành `.env`, điền email và mật khẩu mạnh cho nhóm cần dùng, rồi từ thư mục gốc chạy:

```bash
python seed_accounts.py
```

Script bỏ qua nhóm thiếu email hoặc mật khẩu, từ chối mật khẩu dưới 8 ký tự, và không in mật khẩu/hash. Chạy lại không đổi mật khẩu hoặc vai trò của email đã tồn tại. Đăng ký qua `POST /api/auth/register` luôn tạo `CUSTOMER`, kể cả khi gửi thêm `role`.

### Kiểm thử

```bash
python -m pytest -q
node tests/frontend_xss_smoke.cjs
```

`pytest.ini` giới hạn thu thập vào `tests/`; các script `test_*.py` ở thư mục gốc là script thử tay, không phải pytest suite.

### Lưu ý khi nâng cấp cơ sở dữ liệu

Khi mở một database cũ, ứng dụng tự áp dụng `database/schema.sql` qua `ensure_schema()` trong lúc khởi tạo; các câu lệnh `CREATE TABLE/INDEX IF NOT EXISTS` bổ sung đối tượng còn thiếu mà không xóa dữ liệu hiện có.

Bảng `users` có thể chưa có tài khoản. Dùng mục **Tạo tài khoản demo** phía trên; trong repo không có mật khẩu mặc định. Quyền admin chỉ dành cho role `ADMIN`.

---

## 4. CÁC TÍNH NĂNG TRỌNG TÂM & CÁCH SỬ DỤNG

### 🛒 4.1. Mua Hàng & Chọn Biến Thể Sản Phẩm
1. Duyệt danh mục: Bấm vào các thẻ tab *Áo Nam, Quần Nam, Áo Khoác, Đầm & Váy Nữ*.
2. Bấm **"Xem chi tiết"** vào sản phẩm bất kỳ để mở cửa sổ chi tiết.
3. Chọn màu sắc và kích cỡ (Size S, M, L, XL). Hệ thống sẽ hiển thị tồn kho realtime cho từng biến thể SKU.
4. Bấm **"Thêm vào giỏ hàng"**.

### 💳 4.2. Đặt hàng và thanh toán mô phỏng

Checkout và thanh toán yêu cầu đăng nhập Customer. Tạo tài khoản bằng giao diện đăng ký hoặc cấu hình `CUSTOMER_*` rồi chạy `python seed_accounts.py`. Checkout tạo đơn `PENDING_PAYMENT`, trừ/giữ kho trong transaction SQLite, rồi mở giao diện mô phỏng.

Mô phỏng tạo payload/MAC theo định dạng ZaloPay, nhưng **không gọi API ZaloPay hay ngân hàng thật**. Callback trong ứng dụng cần checksum hợp lệ. Simulator kiểm tra số thẻ mẫu, hạn, CVV (với thẻ tín dụng) và OTP; webhook xử lý idempotent. Đơn pending hết hạn sau 15 phút; app xử lý expiry khi các luồng liên quan gọi `expire_pending_orders()` (ví dụ checkout và các thao tác quản trị), không có tác vụ nền định kỳ.

Thẻ và OTP mẫu trong `services/payment_service.py`:

| Mẫu | Số thẻ | Hạn | CVV | OTP | Kết quả |
|---|---|---|---|---|---|
| Visa | `4111 1111 1111 1111` | `12/28` | `123` | `111111` | Thành công |
| Mastercard | `5555 5555 5555 5555` | `10/27` | `456` | `111111` | Thành công |
| JCB | `3528 0000 0000 0000` | `08/29` | `789` | `111111` | Thành công |
| Visa demo bị từ chối | `4000 0000 0000 0002` | `12/28` | `123` | `111111` | Mô phỏng không đủ số dư |
| Napas NCB | `9704 1985 2619 1432 198` | `07/30` | — | `123456` | Thành công |
| Napas Vietcombank | `9704 3666 1234 5678` | `03/30` | — | `123456` | Thành công |

Ví mô phỏng: ZaloPay `0912345678` và MoMo `0909999888`, cả hai dùng OTP `111111`. Đây là dữ liệu test, không phải tài khoản thanh toán thật.

Transaction tạo đơn dùng `BEGIN IMMEDIATE`/rollback trong Python. SQLite triggers chặn tồn kho âm bằng `RAISE(ABORT)` và ghi log biến động kho/trạng thái đơn; hoàn kho do code Python xử lý khi thanh toán hủy/thất bại.

### 🤖 4.3. Chatbot Trợ Lý Thời Trang RAG
1. Bấm vào nút nổi tròn **"Tư Vấn Chọn Size (RAG AI)"** ở góc dưới bên phải màn hình.
2. Bạn có thể bấm vào các câu hỏi gợi ý nhanh hoặc tự nhập câu hỏi, ví dụ:
   * *"Tôi cao 1m70 nặng 65kg muốn tìm áo sơ mi đi làm"*
   * *"Gợi ý áo khoác chống nước đi phượt"*
   * *"Tìm đầm lụa dự tiệc cưới thanh lịch che khuyết điểm"*
3. Chatbot truy vấn SQLite và trả lời bằng template; khi có `GEMINI_API_KEY`, Gemini chỉ chọn function/tool, còn câu trả lời và sản phẩm được dựng từ kết quả đã kiểm chứng trong DB. Bấm thẻ sản phẩm để xem chi tiết.

### 🔍 4.4. Công Cụ RAG Inspector (Minh Chứng Kỹ Thuật)
* Ở đầu cửa sổ Chatbot, bấm nút **"RAG Trace"**.
* Trace hiển thị `generation_mode`: `template` hoặc `llm_router + template_render`, cùng query tokens, tool calls, sản phẩm truy xuất và điểm cosine. Hệ thống dùng TF-IDF-style lexical weighting + cosine trên SQLite, kèm bộ lọc số đo/size, giá, màu, chất liệu, danh mục và tồn kho; không dùng embedding hay vector database.

### ⚡ 4.5. Kiểm Tra CSDL SQL & Triggers (SQL Audit)
* Trên thanh menu chính, bấm nút **"SQL & Triggers"**.
* Modal hiển thị thống kê sản phẩm/biến thể/đơn hàng và log SQLite triggers `trg_track_order_status`, `trg_log_inventory_change`; endpoint yêu cầu role `ADMIN`.

### Xác thực và phân quyền

Đăng nhập tại `POST /api/auth/login` xác minh email/mật khẩu rồi lưu `user_id` và CSRF token trong Flask session cookie được ký bằng `SECRET_KEY` (hoặc `FLASK_SECRET_KEY` làm fallback của Flask). Mật khẩu băm PBKDF2-HMAC-SHA256 với salt ngẫu nhiên và 600.000 iterations. Role trong DB là `ADMIN`, `STAFF`, `CUSTOMER`; đăng ký `POST /api/auth/register` chỉ tạo `CUSTOMER`. `GET /api/auth/me` và `POST /api/auth/logout` cần đăng nhập; logout cần thêm CSRF. Checkout và các route xử lý thanh toán (`POST /api/orders/checkout`, `/api/payment/process-card`, `/api/payment/simulate-callback`) cần session `CUSTOMER` và CSRF. Các route `/api/admin/stats`, `/api/ai/sync-rag` và route quản trị sản phẩm/biến thể/đơn hàng cần `ADMIN`; route ghi còn cần CSRF. Danh mục và chat (`/api/products`, `/api/ai/chat`) đọc công khai. Không dùng JWT/OAuth.

### Giới hạn đã biết

- Sau checkout/thanh toán thành công, app đồng bộ lại toàn bộ Knowledge Base RAG từ SQLite; phù hợp demo nhỏ nhưng có thể tăng độ trễ khi catalog lớn.
- Rate limit chat là 20 request/phút/IP, lưu trong bộ nhớ của một tiến trình; không chia sẻ giữa nhiều worker.
- `static/js/app.js` chưa được tách thành ES modules.
- Chưa kiểm tra đầy đủ mọi viewport, thao tác bàn phím và focus accessibility.
- `database/store.db` đang được Git theo dõi; pytest hiện dùng DB tạm, không dùng file này.

---

## 5. QUY TRÌNH LÀM VIỆC NHÓM QUA GIT & GITHUB

Nhánh tính năng của nhóm được dùng làm nhánh nền là `feature/ai-rag-payment`; nhánh rà soát hiện tại là `fix/review-improvements`. Tạo nhánh công việc từ nhánh nền, giữ commit theo nhóm thay đổi và mở PR quay lại `feature/ai-rag-payment` sau khi review. Không mặc định kéo hoặc merge `main` trong quy trình này.

```bash
git fetch origin
git switch feature/ai-rag-payment
git pull --ff-only origin feature/ai-rag-payment
git switch -c codex/<ten-cong-viec>
# chỉnh sửa, chạy test, stage đúng file
git add <file-da-xem-xet>
git commit -m "fix(scope): mô tả thay đổi"
git push -u origin codex/<ten-cong-viec>
```

Sau đó tạo PR với base `feature/ai-rag-payment`; nhóm review và gộp theo quy ước repo.

---

## 6. KỊCH BẢN DEMO BÁO CÁO CHO GIẢNG VIÊN

Trước demo, cấu hình `.env`, chạy `python seed_accounts.py`, rồi khởi động `python app.py`. Đăng nhập bằng tài khoản Customer seeded để checkout; dùng tài khoản Admin seeded cho `/admin/dashboard` và SQL Audit.

1. **Checkout và thanh toán:** chọn sản phẩm/biến thể, tạo đơn chờ thanh toán, dùng thẻ Visa `4111 1111 1111 1111`, hạn `12/28`, CVV `123`, OTP `111111` để mô phỏng thành công. Có thể dùng Visa demo bị từ chối `4000 0000 0000 0002` với cùng hạn/CVV/OTP để trình diễn lỗi số dư. Napas NCB `9704 1985 2619 1432 198` hạn `07/30`, OTP `123456`; Napas Vietcombank `9704 3666 1234 5678`, hạn `03/30`, OTP `123456`. Ví ZaloPay `0912345678` hoặc MoMo `0909999888`, OTP `111111`.
2. **SQL Audit:** mở modal để xem số liệu và log SQLite triggers sau trạng thái đơn; transaction đặt hàng và phần hoàn kho nằm trong Python, không phải stored procedure SQL.
3. **Chat/RAG Trace:** hỏi ví dụ “Tôi cao 1m70 nặng 65kg muốn tìm áo sơ mi đi làm”, mở RAG Trace và chỉ ra `generation_mode`, tool/retrieval evidence, bộ lọc catalog và cosine score. Không mô tả kết quả là embedding/vector DB.

---
*Chúc nhóm hoàn thành xuất sắc đồ án Niên luận chuyên ngành Kỹ thuật Phần mềm!* 🎓
