# TÀI LIỆU PHÂN TÍCH YÊU CẦU HỆ THỐNG (SRS)
## ĐỀ TÀI: WEBSITE BÁN QUẦN ÁO TÍCH HỢP CHATBOT AI (RAG) & THANH TOÁN ẢO
**Môn học:** Niên luận Chuyên ngành Kỹ thuật Phần mềm  
**Phiên bản:** 1.0  
**Ngày lập:** 10/10/2026  

---

## 1. TỔNG QUAN DỰ ÁN
Tài liệu này giữ các FR/NFR ban đầu làm mục tiêu yêu cầu; không phải mọi yêu cầu đã được triển khai. Code hiện tại là ứng dụng thương mại điện tử Flask/SQLite có checkout, thanh toán mô phỏng, xác thực bằng session, admin/customer routes và chatbot RAG. Giao dịch đơn hàng là hàm Python điều khiển SQLite transaction (`BEGIN IMMEDIATE`/rollback); các trigger là SQLite triggers. Không có stored procedure MySQL/PostgreSQL.

---

## 2. PHÂN TÍCH YÊU CẦU NGHIỆP VỤ (BUSINESS REQUIREMENTS)

### 2.1. Quy trình Nghiệp vụ Quản lý Sản phẩm & Tồn kho
* **Nhập hàng & Quản lý Biến thể (Variants):** Mỗi sản phẩm thời trang bao gồm nhiều biến thể (Size: S, M, L, XL; Màu sắc: Đen, Trắng, Be...). Hệ thống quản lý số lượng tồn kho theo từng biến thể (SKU) chứ không chỉ theo sản phẩm cha.
* **Cập nhật trạng thái:** Sản phẩm tự động chuyển trạng thái "Hết hàng" khi tất cả biến thể có `stock_quantity = 0`.
* **Ràng buộc trừ kho:** Khi khách hàng đặt hàng và thanh toán thành công, số lượng tồn kho phải được giảm ngay lập tức. Nếu đơn hàng bị hủy hoặc hoàn tiền, số lượng tồn kho phải được hoàn lại chính xác.

### 2.2. Quy trình Nghiệp vụ Mua hàng & Giỏ hàng
* **Khách vãng lai (Guest):** Cho phép xem danh mục sản phẩm, tìm kiếm, lọc theo giá/size/màu, và trò chuyện với Chatbot AI để nhận tư vấn.
* **Khách hàng đăng nhập (Customer):** Thêm sản phẩm vào giỏ hàng, áp dụng mã giảm giá (Voucher), lưu thông tin địa chỉ giao hàng và theo dõi lịch sử đơn hàng.
* **Đồng bộ giỏ hàng:** Khi khách vãng lai đăng nhập, giỏ hàng lưu tạm trong phiên (Session/LocalStorage) sẽ được hợp nhất với giỏ hàng tài khoản trên cơ sở dữ liệu.

### 2.3. Quy trình Nghiệp vụ Thanh toán Ảo (Mock/Sandbox Payment)
* **Khởi tạo giao dịch:** Khi xác nhận thanh toán, đơn hàng được tạo với trạng thái `PENDING_PAYMENT` và sinh mã giao dịch duy nhất (`TransactionCode`).
* **Yêu cầu ban đầu về cổng thanh toán:** Chuyển hướng người dùng sang giao diện thanh toán mô phỏng và cung cấp các kịch bản thử nghiệm:
  * Thanh toán thành công (`SUCCESS`): Cập nhật trạng thái đơn sang `PAID`, kích hoạt trừ tồn kho, gửi thông báo.
  * Hủy thanh toán (`CANCELLED`): Trả lại trạng thái đơn hàng.
  * Lỗi giao dịch (`FAILED`): Cho phép khách hàng chọn thanh toán lại hoặc chọn hình thức COD.
* **Tính bất biến giao dịch (Audit Log):** Mọi sự kiện giao dịch thanh toán đều được lưu vết chi tiết (IP, thời gian, số tiền, mã phản hồi) để phục vụ đối soát.

  **Hiện trạng:** luồng đang chạy là simulator cục bộ với payload/MAC theo định dạng ZaloPay; không gọi API ZaloPay, VNPAY, MoMo hoặc Stripe. Callback checksum, thẻ/OTP mẫu, idempotency và expiry đơn được xử lý trong app/SQLite; không có lưu đầy đủ IP/payload đối soát theo yêu cầu gốc.

### 2.4. Quy trình Nghiệp vụ Chatbot AI Trợ lý Tư vấn Thời trang (RAG)
* **Yêu cầu gốc về chatbot RAG (Retrieval-Augmented Generation):**
  * **Knowledge Base Sản phẩm:** Định kỳ hoặc realtime đồng bộ thông tin quần áo vào kho truy xuất.
  * **Truy vấn tư vấn:** Khách hàng hỏi (ví dụ: *"Tôi cao 1m70, nặng 65kg, muốn tìm áo sơ mi đi tiệc dưới 500k"*).
  * **Trích xuất thông tin & Gợi ý:** Tìm sản phẩm phù hợp, chuyển context cho logic trả lời và kèm liên kết trực tiếp đến sản phẩm.
  * **Giới hạn phạm vi (Guardrails):** Chatbot chỉ trả lời các câu hỏi liên quan đến sản phẩm, tư vấn thời trang, chính sách đổi trả, hướng dẫn mua hàng của cửa hàng; từ chối trả lời các chủ đề ngoài phạm vi.

  **Hiện trạng:** catalog được dựng trong bộ nhớ từ SQLite; truy xuất dùng lexical weighting kiểu TF-IDF kết hợp cosine similarity và bộ lọc catalog, không dùng embedding/vector database. Khi có Gemini key, Gemini chỉ chọn function/tool; Python render câu trả lời từ kết quả SQLite. Nếu không có key, dùng template/local rules.

---

## 3. PHÂN TÍCH YÊU CẦU CHỨC NĂNG (FUNCTIONAL REQUIREMENTS)

### 3.1. Phân hệ Khách hàng (Customer & Guest)
* **FR-01: Quản lý tài khoản:** Đăng ký, đăng nhập (JWT/OAuth), đổi mật khẩu, quản lý sổ địa chỉ giao hàng.
* **FR-02: Duyệt & Tìm kiếm sản phẩm:** Tìm kiếm full-text, lọc đa tiêu chí (danh mục, khoảng giá, size, màu sắc), sắp xếp (bán chạy, giá tăng/giảm, mới nhất).
* **FR-03: Chi tiết sản phẩm:** Xem hình ảnh, bảng kích thước (Size Chart), đánh giá bình luận (Reviews), chọn thuộc tính màu/size để kiểm tra tồn kho realtime.
* **FR-04: Quản lý giỏ hàng:** Thêm/sửa số lượng/xóa sản phẩm khỏi giỏ, áp dụng mã coupon/voucher.
* **FR-05: Đặt hàng & Thanh toán ảo:** Điền thông tin giao hàng, chọn phương thức thanh toán (COD hoặc Thanh toán ảo Sandbox), nhận thông báo kết quả giao dịch và mã đơn hàng.
* **FR-06: Tra cứu đơn hàng:** Xem lịch sử mua hàng, chi tiết trạng thái đơn (Chờ xử lý, Đã thanh toán, Đang giao, Đã giao, Đã hủy).
* **FR-07: Tương tác Chatbot AI:**
  * Widget trò chuyện nổi ở góc màn hình.
  * Gợi ý câu hỏi mẫu: "Tư vấn chọn size", "Mẫu áo hot trend tuần này", "Chính sách đổi trả".
  * Nhận phản hồi tư vấn kèm thẻ sản phẩm (Product Card: ảnh, tên, giá, nút xem ngay).

### 3.2. Phân hệ Quản trị viên (Admin)
* **FR-08: Quản lý danh mục & sản phẩm:** Thêm/sửa/xóa mềm (Soft Delete) danh mục, sản phẩm, và các biến thể (SKUs). Quản lý thư viện hình ảnh sản phẩm.
* **FR-09: Quản lý kho hàng:** Theo dõi số lượng tồn kho theo SKU, cảnh báo khi mặt hàng sắp hết (`stock <= threshold`), tạo phiếu nhập kho.
* **FR-10: Quản lý đơn hàng:** Tiếp nhận đơn, cập nhật trạng thái vận chuyển, xử lý hoàn hủy đơn.
* **FR-11: Quản lý khuyến mãi:** Tạo và kích hoạt mã giảm giá (phần trăm, số tiền cố định, điều kiện đơn tối thiểu).
* **FR-12: Quản lý dữ liệu RAG AI:** Nút đồng bộ (Sync) dữ liệu sản phẩm mới vào Vector Database; xem nhật ký hội thoại của khách để cải thiện câu trả lời.
* **FR-13: Báo cáo & Thống kê Dashboard:** Biểu đồ doanh thu theo ngày/tháng, top sản phẩm bán chạy, tỷ lệ chuyển đổi thanh toán online.

### 3.3. Phân hệ Dịch vụ AI & Thanh toán (Services)
* **FR-14: Embedding & Vector Retrieval:** Tự động tạo embedding vector từ mô tả sản phẩm và bảng size; tìm kiếm sản phẩm tương đồng ngữ nghĩa theo truy vấn người dùng.
* **FR-15: Prompt Engine & LLM Orchestrator:** Xây dựng prompt chứa bối cảnh kho hàng thực tế (chỉ gợi ý các sản phẩm còn hàng).
* **FR-16: Virtual Payment Simulator:** Cung cấp API mô phỏng Webhook IPN (Instant Payment Notification), xử lý chữ ký điện tử mô phỏng (Checksum HMAC-SHA256) đảm bảo an toàn giao dịch.

---

## 4. PHÂN TÍCH YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS)

### 4.1. Hiệu năng & Khả năng mở rộng (Performance & Scalability)
* **NFR-01 (Thời gian phản hồi):** API danh sách sản phẩm và chi tiết sản phẩm phản hồi `< 200ms` với dữ liệu từ 10.000 sản phẩm trở lên (nhờ Indexing và tối ưu truy vấn).
* **NFR-02 (Tốc độ Chatbot AI):** Chatbot trả lời trong vòng `< 2.5s` (sử dụng streaming response để người dùng thấy câu trả lời xuất hiện ngay tức thì).
* **NFR-03 (Tối ưu hóa Database):** Tất cả các câu truy vấn phức tạp (báo cáo doanh thu, tìm kiếm nhiều bộ lọc) được đóng gói trong **Stored Procedures** và tận dụng **B-Tree Indexes**, không quét toàn bảng (Full Table Scan).

### 4.2. Tính toàn vẹn & Ràng buộc dữ liệu SQL (Data Integrity & Consistency)
* **NFR-04 (ACID & Triggers):** Áp dụng Database Transaction cho chu trình đặt hàng.
  * Sử dụng **Trigger** kiểm tra số lượng tồn kho trước khi chèn vào `order_items`.
  * Tự động trừ tồn kho hoặc từ chối đơn nếu thiếu hàng ngay ở tầng cơ sở dữ liệu.
* **NFR-05 (Audit Trail Trigger):** Trigger ghi lại lịch sử thay đổi trạng thái đơn hàng (`order_status_history`) và biến động giá sản phẩm.

### 4.3. Bảo mật (Security)
* **NFR-06 (Xác thực & Phân quyền):** Sử dụng JWT Token (Access Token hạn ngắn + Refresh Token), phân quyền dựa trên Role (RBAC: `ROLE_CUSTOMER`, `ROLE_ADMIN`).
* **NFR-07 (Chống tấn công phổ biến):** Bảo vệ chống SQL Injection (Prepared Statements / Stored Procedures), XSS, CSRF, và Rate Limiting trên các endpoint gọi Chatbot AI để tránh spam quota API.
* **NFR-08 (Mã hóa mật khẩu):** Mật khẩu người dùng được băm an toàn bằng BCrypt (salt rounds >= 10).

### 4.4. Tính khả dụng & Trải nghiệm (Usability & Reliability)
* **NFR-09 (Responsive Design):** Giao diện hoạt động trơn tru trên cả Desktop, Tablet và Mobile.
* **NFR-10 (Error Handling):** Hệ thống có cơ chế xử lý lỗi tập trung (Global Exception Handler); trả về mã lỗi HTTP chuẩn và thông điệp thân thiện với người dùng.

---

## PHẠM VI THỰC HIỆN

Các FR/NFR gốc phía trên được giữ nguyên như yêu cầu mục tiêu. Trạng thái dưới đây mô tả code hiện tại; yêu cầu gốc không được hiểu là đã triển khai chỉ vì có mặt trong SRS.

| Mã | Trạng thái | Bằng chứng hiện trạng |
|---|---|---|
| FR-01 | Làm một phần | `app.py` dùng register/login và session; `database/db.py` băm PBKDF2; `tests/test_seed_accounts.py` kiểm tra đăng nhập. Chưa có đổi mật khẩu/address book; không dùng JWT/OAuth. |
| FR-02 | Làm một phần | `app.py:api_products` và `database/db.py:get_all_products` hỗ trợ search/category; RAG lọc giá/size/màu/chất liệu/tồn. Chưa có full-text, sắp xếp theo bán chạy hoặc nhiều bộ lọc storefront. |
| FR-03 | Làm một phần | `templates/product_detail.html`, `database/db.py:get_product_by_id`, `services/size_chart.py`; không có hệ thống reviews/comments. |
| FR-04 | Làm một phần | `static/js/app.js` giữ cart phía client; `tests/test_review_backend.py::test_invalid_quantities_are_rejected_without_changing_stock` kiểm tra giới hạn server. Không có coupon/voucher. |
| FR-05 | Làm một phần | `database/db.py:sp_create_order_and_deduct_stock` và `tests/test_review_backend.py` kiểm tra đặt hàng/payment; checkout dùng simulator, chưa có luồng COD hoàn chỉnh hay thông báo giao dịch ngoài giao diện. |
| FR-06 | Làm một phần | `customer_portal.py` và `services/agentic_tools.py:db_lookup_order_for_customer` có tra đơn; `tests/test_rag_quality.py` kiểm tra auth/ownership. Không có mọi trạng thái hay lịch sử giao dịch/IP theo yêu cầu gốc. |
| FR-07 | Đã làm | `services/agentic_rag.py`, `static/js/stylist-chat.js`; `tests/test_chat_regression.py` và `tests/test_rag_quality.py` kiểm tra intent, truy xuất, size và guardrails. |
| FR-08 | Làm một phần | `admin_products.py`, `admin_variants.py` cho CRUD sản phẩm/biến thể và publish toggle; chưa có CRUD danh mục hoặc thư viện ảnh riêng. |
| FR-09 | Làm một phần | Tồn theo SKU trong `database/db.py`; `admin_dashboard.py` đếm low-stock; chưa có phiếu nhập kho. |
| FR-10 | Làm một phần | `admin_orders.py` xem/cập nhật đơn; `tests/test_review_backend.py` kiểm tra webhook/hủy/hoàn tồn. Chưa có workflow vận chuyển/hoàn tiền đầy đủ. |
| FR-11 | Chưa làm (để phát triển sau) | Không có promotion/coupon model hoặc route trong `database/schema.sql`, `admin_*.py`. |
| FR-12 | Làm một phần | `app.py:api_sync_rag`, `services/rag_engine.py:sync_knowledge_base` và RAG Trace; `tests/test_review_backend.py::test_admin_stats_and_rag_sync_require_existing_admin_role`. Không có vector DB hoặc nhật ký hội thoại quản trị. |
| FR-13 | Làm một phần | `admin_dashboard.py` và `database/db.py:get_db_stats` cung cấp counts/summary/logs; chưa có biểu đồ doanh thu theo thời gian, top seller hay conversion. |
| FR-14 | Chưa làm (để phát triển sau) | `services/rag_engine.py` dùng lexical weighting/cosine, không tạo embedding hoặc kết nối vector database; `tests/test_rag_quality.py` kiểm tra retriever hiện tại. |
| FR-15 | Làm một phần | `services/agentic_rag.py` gọi Gemini function-calling để chọn tool và code dựng câu trả lời; `tests/test_chat_regression.py::test_agentic_trace_identifies_gemini_router_with_template_rendering`. Không dùng LLM để viết câu trả lời cuối. |
| FR-16 | Đã làm | `services/payment_service.py`, `database/db.py:sp_process_payment_webhook`; `tests/test_review_backend.py` kiểm tra checksum, idempotency, OTP và expiry. Đây là simulator, không phải IPN từ gateway thật. |
| NFR-01 | Làm một phần | `database/schema.sql` có index cho catalog/variants/orders/payments; chưa có benchmark chứng minh `<200ms` ở 10.000 sản phẩm. |
| NFR-02 | Làm một phần | `app.py:api_ai_chat` hỗ trợ response NDJSON; chưa có đo SLA `<2.5s` hoặc benchmark tải. |
| NFR-03 | Làm một phần | `database/db.py` có Python transaction helpers và schema indexes; không có stored procedures SQL, báo cáo truy vấn hay bằng chứng không full-scan cho mọi truy vấn. |
| NFR-04 | Làm một phần | `database/db.py:sp_create_order_and_deduct_stock` kiểm tra/trừ kho trong transaction `BEGIN IMMEDIATE`/rollback; `database/schema.sql` dùng trigger SQLite `RAISE(ABORT)` để chặn tồn âm khi UPDATE. Trigger không kiểm tra/trừ kho tại INSERT `order_items` như yêu cầu gốc; `tests/test_review_backend.py` kiểm tra rollback/oversell. |
| NFR-05 | Làm một phần | SQLite triggers `trg_track_order_status` và `trg_log_inventory_change` ghi status/stock; không có trigger audit biến động giá. |
| NFR-06 | Làm một phần | `app.py:require_login`, `require_admin`, `require_customer_payment` dùng session và role; `tests/test_seed_accounts.py` kiểm tra admin/customer. Không dùng JWT access/refresh token. |
| NFR-07 | Làm một phần | SQL parameterization, CSRF, escaping, callback validation và chat rate limit có trong `app.py`, `static/js/*.js`; `tests/test_review_backend.py`/`tests/frontend_xss_smoke.cjs` bao phủ một số trường hợp, không phải audit bảo mật đầy đủ. |
| NFR-08 | Làm một phần | `database/db.py:_hash_password` dùng PBKDF2-HMAC-SHA256, salt ngẫu nhiên, 600.000 iterations; không dùng BCrypt như yêu cầu gốc. |
| NFR-09 | Làm một phần | CSS responsive có trong `static/css/` và templates; chưa xác minh đầy đủ mọi viewport/keyboard/accessibility. |
| NFR-10 | Đã làm | `app.py:handle_http_error`, `handle_unexpected_error`; `tests/test_review_backend.py::test_chat_limit_and_http_errors_use_consistent_json` kiểm tra JSON lỗi và không lộ chi tiết 500. |

---

## 5. CẤU TRÚC CƠ SỞ DỮ LIỆU SQLITE HIỆN TẠI

### 5.1. Danh sách các Bảng Dữ liệu (Tables)
1. `users` (id, email, password_hash, full_name, phone, role, is_active, created_at)
2. `customer_order_links` (order_id, user_id) — liên kết customer với đơn; đơn guest cũ có thể không có liên kết.
3. `categories` (id, name, slug, description, is_active)
4. `products` (id, category_id, name, slug, price, discount_price, material, style, size_guide, description, image_url, is_published, created_at)
5. `product_variants` (id, product_id, sku, color, size, stock_quantity, created_at)
6. `orders` (id, order_code, customer_name, customer_phone, customer_address, total_amount, status, payment_method, created_at)
7. `order_items` (id, order_id, variant_id, quantity, unit_price, subtotal)
8. `payments` (id, order_id, transaction_code, amount, payment_gateway, status, checksum_signature, created_at)
9. `inventory_logs` (id, variant_id, change_quantity, remaining_stock, reason, created_at)
10. `order_status_history` (id, order_id, old_status, new_status, note, changed_at)

Schema hiện ở [database/schema.sql](database/schema.sql); `database/db.py:ensure_schema()` áp schema idempotent khi khởi tạo/đầu kết nối. Vai trò hợp lệ là `ADMIN`, `STAFF`, `CUSTOMER`.

### 5.2. Danh mục Chỉ mục (Indexes) để Tối ưu Truy vấn
* `idx_products_category` trên `(category_id, is_published)`.
* `idx_products_price` trên `(discount_price, price)`.
* `idx_variants_product` trên `product_id`.
* `idx_orders_code` trên `order_code` (cột cũng có UNIQUE constraint).
* `idx_payments_transaction` trên `transaction_code` (cột cũng có UNIQUE constraint).
* `idx_customer_order_user` trên `customer_order_links.user_id`; email có UNIQUE index SQLite tạo tự động.

### 5.3. Python transaction helpers (không phải stored procedures SQL)
1. `database/db.py:sp_create_order_and_deduct_stock` nhận giỏ hàng, mở `BEGIN IMMEDIATE`, kiểm tra và ghi order/items/payment, trừ kho; rollback khi lỗi.
2. `database/db.py:sp_process_payment_webhook` cập nhật giao dịch còn PENDING và đơn còn PENDING_PAYMENT; callback lặp không hoàn kho lần hai.
3. `database/db.py:expire_pending_orders` chuyển đơn PENDING quá 15 phút qua nhánh CANCELLED để hoàn kho.
4. `sp_*` là tên hàm Python tương thích code hiện tại, không phải stored procedure được khai báo trong SQLite. Không có `sp_GetMonthlyRevenueReport`.

### 5.4. Danh mục Triggers (Ràng buộc Nghiệp vụ Tự động)
1. `trg_prevent_negative_stock`: BEFORE UPDATE trên `product_variants.stock_quantity`, dùng `RAISE(ABORT, ...)` của SQLite nếu giá trị mới âm.
2. `trg_track_order_status`: AFTER UPDATE trạng thái `orders`, ghi `order_status_history` khi trạng thái đổi.
3. `trg_log_inventory_change`: AFTER UPDATE tồn kho, ghi lượng thay đổi và tồn còn lại vào `inventory_logs`.

Trừ kho/hoàn kho do Python transaction xử lý; trigger không tự giảm kho khi payment chuyển PAID.

---

## 6. KIẾN TRÚC RAG MỤC TIÊU TRONG YÊU CẦU GỐC (CHƯA TRIỂN KHAI)

Sơ đồ dưới đây giữ lại yêu cầu gốc về embedding/vector DB; đây là kiến trúc mục tiêu để phát triển sau, không phải mô tả hệ thống đang chạy.

```
[Người dùng đặt câu hỏi]
          │
          ▼
┌───────────────────────────────┐
│     Backend AI Controller     │
└──────────────┬────────────────┘
               │ (1) Embedding truy vấn
               ▼
┌───────────────────────────────┐
│  Vector Database (ChromaDB)   │ <─── [Đồng bộ sản phẩm định kỳ từ SQL]
└──────────────┬────────────────┘
               │ (2) Top-K sản phẩm phù hợp nhất (Tên, mô tả, size, còn hàng)
               ▼
┌───────────────────────────────┐
│        Prompt Builder         │
│  (System prompt + Context)    │
└──────────────┬────────────────┘
               │ (3) Gửi ngữ cảnh thực tế vào LLM
               ▼
┌───────────────────────────────┐
│     Gemini / OpenAI API       │
└──────────────┬────────────────┘
               │ (4) Trả lời gợi ý & link sản phẩm
               ▼
[Mục tiêu yêu cầu: khách hàng nhận tư vấn dựa trên kho hiện tại]
```

### 6.1. Luồng RAG đang triển khai

`services/rag_engine.py` đồng bộ catalog từ SQLite vào bộ nhớ, tạo token và trọng số từ vựng kiểu TF-IDF, tính cosine similarity, rồi áp bộ lọc số đo, giá, màu, size, chất liệu và tồn kho. Không tạo embedding và không kết nối vector database. `services/agentic_rag.py` dùng Gemini (nếu có `GEMINI_API_KEY`) để chọn function/tool; Python xác minh đối số, lấy dữ liệu từ SQLite và dựng câu trả lời. Khi không có key hoặc không dùng router Gemini, trace hiển thị `generation_mode: template`; khi Gemini chọn tool và kết quả được dựng theo template, trace hiển thị `generation_mode: llm_router + template_render`.
