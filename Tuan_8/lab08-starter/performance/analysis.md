# Lab 4 — Phân tích kết quả

Môi trường đo: Flask development server + SQLite, Locust và server cùng chạy trên một máy cá nhân. Mỗi kịch bản chạy một lần. Lỗi 1% của `GET /books?year=` là lỗi giả lập phía client (`response.failure()` trong Locust), server không trả HTTP 500.

| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | 22 | 1.42% (2/141) | 5.0 |
| B | 50 | 5 | 60s | 22 | 0.07% (1/1380) | 23.6 |
| C | 200 | 50 | 30s | 100 | 0.18% (5/2826) | 97.0 |

## 1. Kịch bản có p95 cao nhất

Kịch bản C (200 user) có p95 tổng là 100 ms, còn A và B đều là 22 ms. Trong C, độ trễ tăng ở mọi endpoint: p95 của `GET /books` là 100 ms, `GET /books/{id}` là 98 ms, `GET /books?year=` là 88 ms, `POST /books` là 120 ms; trong B các giá trị này lần lượt là 12, 18, 17 và 38 ms. Giá trị lớn nhất của C là 356 ms (B là 70 ms). `POST /books` chậm nhất ở cả ba kịch bản. Nguyên nhân có khả năng là SQLite chỉ cho một thao tác ghi tại một thời điểm và Flask development server xử lý song song hạn chế; phần này là suy luận từ cấu hình, chưa được kiểm chứng bằng profiling.

## 2. Endpoint tăng failure rate

Chỉ `GET /books?year=` có lỗi, và toàn bộ lỗi trong `Error report` là `injected client-side failure (1%), server returned no 500`. Không có HTTP 500, timeout hay lỗi kết nối nào do server gây ra. Tỉ lệ lỗi không tăng theo số user: 1.42%, 0.07%, 0.18%. Task tìm kiếm chiếm khoảng 15% lưu lượng nên tỉ lệ lỗi tổng kỳ vọng khoảng 0.15%; kịch bản A cao hơn chỉ vì mẫu nhỏ (141 request, 2 lỗi). Response 404 của `GET /books/{id}` được đánh dấu thành công có chủ đích vì id ngẫu nhiên có thể không tồn tại.

## 3. SLO p95 < 300 ms

Cả ba kịch bản đều đạt (22, 22 và 100 ms). Giới hạn của phép đo: dùng SQLite và Flask development server, load generator chạy cùng máy với server nên tranh CPU, mạng là localhost nên không có độ trễ mạng, chạy ngắn 30 đến 60 giây, cơ sở dữ liệu ít dòng, mỗi kịch bản chỉ đo một lần. Ở 200 user p95 mới là 100 ms nên chưa tìm ra ngưỡng quá tải. Vì vậy kết quả không đủ để khẳng định SLO cho production.

Đề xuất baseline cho CI gate: chạy kịch bản B (50 user, 60 giây), fail pipeline nếu p95 tổng vượt 150 ms hoặc có bất kỳ response HTTP 5xx. Ngưỡng 150 ms cao hơn giá trị đo 22 ms để chừa chỗ cho máy CI chậm hơn máy cá nhân, và vẫn thấp hơn SLO 300 ms để phát hiện suy giảm sớm.

## 4. Connection pool giới hạn 5

Kế hoạch kiểm chứng (chưa chạy): truyền `SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 5, "max_overflow": 0, "pool_timeout": 1}` qua tham số `config` của `create_app()`, chạy lại kịch bản C và so sánh với kết quả hiện tại. Nếu 200 user tranh 5 kết nối, kỳ vọng thấy p95 tăng và xuất hiện lỗi HTTP 500 thật từ server (`QueuePool limit ... timed out`) trong `Error report`. Số lỗi 500 này phân biệt được với lỗi giả lập phía client nhờ nội dung thông báo lỗi.
