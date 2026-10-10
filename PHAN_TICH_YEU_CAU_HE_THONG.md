# TÀI LIỆU PHÂN TÍCH YÊU CẦU HỆ THỐNG (SRS)
## ĐỀ TÀI: WEBSITE BÁN QUẦN ÁO TÍCH HỢP CHATBOT AI (RAG) & THANH TOÁN ẢO
**Môn học:** Niên luận Chuyên ngành Kỹ thuật Phần mềm  
**Phiên bản:** 1.0  
**Ngày lập:** 10/10/2026  

---

## 1. TỔNG QUAN DỰ ÁN
Hệ thống là một nền tảng thương mại điện tử chuyên ngành thời trang (quần áo), kết hợp công nghệ Trí tuệ nhân tạo (AI RAG Chatbot) nhằm tối ưu trải nghiệm mua sắm, tự động tư vấn size, phối đồ, và giải đáp thắc mắc về đơn hàng. Hệ thống tích hợp cổng thanh toán trực tuyến mô phỏng (Sandbox/Virtual Payment) và sử dụng cơ sở dữ liệu quan hệ (SQL) được tối ưu hóa sâu với CRUD, Indexes, Stored Procedures và Triggers nhằm đảm bảo tính toàn vẹn dữ liệu và hiệu năng truy vấn.

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
* **Cổng thanh toán ảo:** Chuyển hướng người dùng sang giao diện thanh toán mô phỏng (tương tự VNPAY / MoMo / Stripe Test). Cung cấp các kịch bản thử nghiệm:
  * Thanh toán thành công (`SUCCESS`): Cập nhật trạng thái đơn sang `PAID`, kích hoạt trừ tồn kho, gửi thông báo.
  * Hủy thanh toán (`CANCELLED`): Trả lại trạng thái đơn hàng.
  * Lỗi giao dịch (`FAILED`): Cho phép khách hàng chọn thanh toán lại hoặc chọn hình thức COD.
* **Tính bất biến giao dịch (Audit Log):** Mọi sự kiện giao dịch thanh toán đều được lưu vết chi tiết (IP, thời gian, số tiền, mã phản hồi) để phục vụ đối soát.

### 2.4. Quy trình Nghiệp vụ Chatbot AI Trợ lý Tư vấn Thời trang (RAG)
* **Cơ chế RAG (Retrieval-Augmented Generation):**
  * **Knowledge Base Sản phẩm:** Định kỳ hoặc realtime đồng bộ thông tin quần áo (tên, mô tả chất liệu, bảng size, màu sắc, phong cách, giá bán, tình trạng còn hàng) vào Cơ sở dữ liệu Vector (ChromaDB / pgvector / Pinecone / Qdrant).
  * **Truy vấn tư vấn:** Khách hàng hỏi (ví dụ: *"Tôi cao 1m70, nặng 65kg, muốn tìm áo sơ mi đi tiệc dưới 500k"*).
  * **Trích xuất thông tin & Gợi ý:** Hệ thống semantic search tìm kiếm các sản phẩm phù hợp nhất trong kho dữ liệu, chuyển kèm ngữ cảnh (Context) vào LLM (Gemini / OpenAI) để sinh câu trả lời tư vấn lịch sự, kèm liên kết trực tiếp đến sản phẩm.
  * **Giới hạn phạm vi (Guardrails):** Chatbot chỉ trả lời các câu hỏi liên quan đến sản phẩm, tư vấn thời trang, chính sách đổi trả, hướng dẫn mua hàng của cửa hàng; từ chối trả lời các chủ đề ngoài phạm vi.

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

## 5. THIẾT KẾ CƠ SỞ DỮ LIỆU SQL NÂNG CAO

### 5.1. Danh sách các Bảng Dữ liệu (Tables)
1. `users` (id, email, password_hash, full_name, phone, role, created_at)
2. `categories` (id, name, slug, parent_id, is_active)
3. `products` (id, category_id, name, slug, description, material, price, discount_price, is_published, created_at)
4. `product_variants` (id, product_id, sku, color, size, stock_quantity, image_url)
5. `orders` (id, user_id, order_code, total_amount, discount_amount, final_amount, status, shipping_address, created_at)
6. `order_items` (id, order_id, variant_id, quantity, unit_price, subtotal)
7. `payments` (id, order_id, transaction_code, payment_method, amount, status, response_payload, created_at)
8. `inventory_logs` (id, variant_id, change_type, quantity_change, note, created_at)
9. `order_status_history` (id, order_id, old_status, new_status, changed_by, changed_at)

### 5.2. Danh mục Chỉ mục (Indexes) để Tối ưu Truy vấn
* `idx_products_category_published`: B-Tree composite index trên `(category_id, is_published)` tăng tốc duyệt theo danh mục.
* `idx_products_price`: Index trên cột `discount_price` phục vụ việc lọc và sắp xếp theo giá.
* `idx_variants_product`: Index trên `product_id` để nạp nhanh toàn bộ biến thể size/màu khi xem chi tiết.
* `idx_orders_user_created`: Composite index `(user_id, created_at DESC)` tăng tốc tra cứu lịch sử mua hàng cá nhân.
* `idx_payments_transcode`: Unique index trên `transaction_code` để tìm kiếm tức thì khi webhook thanh toán trả về.

### 5.3. Danh mục Stored Procedures (Thủ tục Lưu trữ)
1. `sp_CreateOrderAndDeductStock`:
   * Nhận vào thông tin khách hàng, danh sách các item (variant_id, quantity).
   * Mở Transaction: kiểm tra tồn kho, tạo bản ghi `orders` và `order_items`, ghi nhận `payments` tạm thời, trừ tồn kho. Rollback nếu bất kỳ biến thể nào không đủ hàng.
2. `sp_ProcessPaymentWebhook`:
   * Tiếp nhận kết quả thanh toán từ cổng ảo.
   * Cập nhật bảng `payments` và chuyển trạng thái đơn hàng trong `orders`.
   * Ghi nhận log thay đổi.
3. `sp_GetMonthlyRevenueReport`:
   * Tổng hợp doanh thu, số đơn hoàn thành, số đơn hủy, giá trị đơn trung bình (AOV) theo từng tháng/năm phục vụ trang Dashboard Admin.

### 5.4. Danh mục Triggers (Ràng buộc Nghiệp vụ Tự động)
1. `trg_AfterOrderPaid_LogInventory`:
   * Khi trạng thái đơn hàng đổi sang `PAID`, trigger tự động ghi bản ghi vào bảng `inventory_logs` để theo dõi nhật ký xuất kho.
2. `trg_PreventNegativeStock`:
   * Trigger chặn thao tác `UPDATE` trên `product_variants` nếu `stock_quantity < 0`, bắn ra ngoại lệ SQL `SIGNAL SQLSTATE '45000'` kèm thông báo lỗi cụ thể.
3. `trg_TrackOrderStatusChange`:
   * Trigger tự động bắt sự kiện `UPDATE` trên cột `status` của bảng `orders` để chèn 1 dòng mới vào bảng `order_status_history`.

---

## 6. KIẾN TRÚC TÍCH HỢP RAG (RETRIEVAL-AUGMENTED GENERATION)

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
[Khách hàng nhận tư vấn chính xác 100% dựa trên kho hiện tại]
```
