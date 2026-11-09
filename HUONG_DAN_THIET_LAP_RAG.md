# Hướng dẫn RAG cho website bán quần áo

## 1. RAG trong dự án này

RAG (Retrieval-Augmented Generation) là quy trình lấy dữ liệu liên quan từ một kho tri thức, đưa dữ liệu đó vào ngữ cảnh rồi tạo câu trả lời. Trong dự án, kho tri thức được tạo từ các sản phẩm đang hiển thị trong SQLite, gồm tên, danh mục, giá, chất liệu, phong cách, bảng size, mô tả và tồn kho biến thể.

**Lưu ý về triển khai:** hệ thống hiện dùng TF-IDF và cosine similarity để truy xuất, sau đó tạo câu trả lời bằng mẫu cục bộ dựa trên sản phẩm và bảng size. `augmented_prompt` được trả về để quan sát hoặc tích hợp LLM sau này; dự án hiện chưa gửi prompt tới ChatGPT, Gemini hay một mô hình ngôn ngữ nào. Vì vậy, đây là RAG có phản hồi xác định, không phải LLM sinh văn bản.

## 2. Luồng xử lý

```text
SQLite
  -> lập tài liệu và chỉ mục TF-IDF trong bộ nhớ
  -> chuẩn hóa câu hỏi, trích số đo
  -> xếp hạng sản phẩm theo nội dung + size phù hợp + tồn kho
  -> ghép retrieved context vào prompt để trace
  -> tạo câu trả lời cục bộ và trả sản phẩm gợi ý
```

### Bước 1: Nạp và lập chỉ mục

`RAGEngine` gọi `sync_knowledge_base()` khi khởi tạo. Hàm lấy các sản phẩm đang xuất bản qua `get_all_products()`, kết hợp thông tin biến thể và xây dựng một tài liệu cho mỗi sản phẩm. Các trường được lập chỉ mục riêng với trọng số:

| Trường | Trọng số |
|---|---:|
| Tên sản phẩm | 3.0 |
| Danh mục | 2.0 |
| Chất liệu, phong cách | 1.5 |
| Bảng size | 1.2 |
| Mô tả | 1.0 |
| Biến thể | 0.8 |

Chuẩn hóa văn bản chuyển chữ về dạng thường, bỏ dấu tiếng Việt và giữ các token như `1m70`, `65kg`. IDF được tính theo số sản phẩm chứa token, giúp giảm ảnh hưởng của các từ xuất hiện ở hầu hết tài liệu. Toàn bộ chỉ mục ở trong bộ nhớ tiến trình, không có vector database bên ngoài.

### Bước 2: Truy xuất sản phẩm

`retrieve()` tạo vector TF-IDF cho câu hỏi và từng tài liệu, sau đó tính cosine similarity. Kết quả được tăng điểm khi chiều cao/cân nặng khớp một khoảng trong bảng size và size đó đang còn hàng; sản phẩm hết toàn bộ hàng bị loại. Mặc định trả tối đa ba sản phẩm.

Ví dụ câu hỏi: *“Tôi cao 1m70 nặng 64kg, tìm áo sơ mi đi tiệc”*. Cụm từ sản phẩm giúp tìm tài liệu áo sơ mi; số đo được kiểm tra với từng khoảng trong bảng size, thay vì chỉ so chính xác chuỗi `1m70` hoặc `64kg`. Nếu size phù hợp đã hết hàng, hệ thống không nói size đó còn hàng.

Điểm số là điểm xếp hạng nội bộ (cosine TF-IDF cộng điểm số đo), không phải xác suất đúng hay “độ hiểu ngữ nghĩa” của mô hình AI.

### Bước 3: Tăng cường ngữ cảnh

`build_augmented_prompt()` ghép các tài liệu được truy xuất vào prompt cùng quy tắc chỉ dùng thông tin trong kho. Prompt được đính kèm `rag_trace` để kiểm tra, nhưng hiện chưa được gửi tới LLM.

### Bước 4: Tạo phản hồi và trace

`generate_response()` tạo câu trả lời từ dữ liệu của sản phẩm xếp hạng đầu tiên: tên, danh mục, giá, chất liệu, phong cách, số size phù hợp và các biến thể còn hàng. Nếu không tìm thấy sản phẩm còn hàng đủ phù hợp, bot thông báo không tìm thấy thay vì tự tạo thông tin. Câu trả lời là mẫu cục bộ, không phải nội dung do LLM sinh.

`rag_trace` bao gồm token truy vấn, phương thức truy xuất, chiều cao/cân nặng đã trích xuất, danh sách sản phẩm kèm điểm lexical/tổng, size đề xuất, đoạn tài liệu và prompt tăng cường.

## 3. API và đồng bộ dữ liệu

- `POST /api/ai/chat`, JSON `{ "message": "..." }`: truy xuất và tạo phản hồi.
- `POST /api/ai/sync-rag`: đọc lại dữ liệu SQL và lập chỉ mục trong bộ nhớ.
- Sau một số luồng cập nhật kho/đặt hàng, ứng dụng gọi `sync_knowledge_base()` để cập nhật tồn kho được truy xuất.

Nếu thay đổi sản phẩm trực tiếp trong SQL hoặc chạy nhiều worker Flask, cần đồng bộ lại trên từng tiến trình để chỉ mục trong bộ nhớ phản ánh dữ liệu mới.

## 4. Giới hạn và hướng phát triển

- TF-IDF so khớp từ khóa, không hiểu từ đồng nghĩa hoặc ngữ cảnh sâu như embedding/LLM.
- Bộ đọc size hỗ trợ định dạng bảng size dạng văn bản phổ biến của dữ liệu mẫu; định dạng mới có thể cần mở rộng parser.
- Tồn kho có thể thay đổi giữa thời điểm lập chỉ mục và lúc khách đặt hàng. Quy trình đặt hàng vẫn phải kiểm tra lại tồn kho trong SQL.
- Muốn có câu trả lời do LLM sinh, cần cấu hình nhà cung cấp/model và gửi `augmented_prompt` tới dịch vụ đó. Không được coi prompt trace hiện tại là bằng chứng đã gọi LLM.

## 5. Kiểm tra nhanh

1. Khởi chạy ứng dụng và hỏi: *“Tôi cao 1m70 nặng 64kg muốn tìm áo sơ mi đi tiệc”*.
2. Xem câu trả lời, size được khớp theo bảng hướng dẫn và các màu/size đang còn tồn.
3. Mở **RAG Trace** để xem token, điểm truy xuất, số đo, size đề xuất và prompt.
4. Thử một câu hỏi không liên quan hoặc sản phẩm hết hàng để xác nhận bot không tự khẳng định thông tin không có trong kho.

Chạy kiểm thử bằng:

```powershell
python -m unittest discover -s tests -v
```
