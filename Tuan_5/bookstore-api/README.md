# Bookstore API - Pagination (Bài 2, Buổi 5)

Flask + SQLAlchemy. Endpoint `GET /api/v1/books` hỗ trợ:

- Phân trang **offset** và **cursor** (chọn qua `?strategy=offset|cursor`, mặc định `cursor`)
- Lọc theo thể loại: `?genre=tech` (so khớp `slug` của Category)
- Sort nhiều khóa: `?sort=-price,title` (dấu `-` = giảm dần)

## Cài đặt & chạy

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python seed.py                  # tạo 50 sách mẫu (chạy 1 lần)
python app.py                   # server tại http://localhost:5000
```

## Chạy test

```bash
pytest -v
```

## Tham số

| Tham số    | Mặc định | Ý nghĩa                                                         |
|------------|----------|-----------------------------------------------------------------|
| strategy   | cursor   | `cursor` hoặc `offset`                                          |
| limit      | 20       | Số item mỗi trang, tối đa 100                                   |
| offset     | 0        | Chỉ dùng khi `strategy=offset`                                  |
| cursor     | (không)  | Chỉ dùng khi `strategy=cursor`; lấy từ `pagination.next_cursor` |
| genre      | (không)  | Slug thể loại, ví dụ `tech`, `novel`, `science`                 |
| sort       | -id      | Gồm: `id`, `title`, `price`, `stock`; nhiều khóa cách nhau bằng `,` |

## Ví dụ

```bash
# Cursor (mặc định)
curl "localhost:5000/api/v1/books?limit=5"
curl "localhost:5000/api/v1/books?limit=5&cursor=<next_cursor>"

# Offset (có total)
curl "localhost:5000/api/v1/books?strategy=offset&offset=10&limit=5"

# Filter + sort nhiều khóa
curl "localhost:5000/api/v1/books?genre=tech&sort=-price,title"
```

Response (cursor):

```json
{
  "data": [ { "id": "book_50", "title": "Book 50", "price": {"amount": 200000, "currency": "VND"}, "...": "..." } ],
  "pagination": { "strategy": "cursor", "limit": 20, "next_cursor": "eyJz...", "has_more": true }
}
```

Response (offset): `pagination` gồm `strategy`, `offset`, `limit`, `total`, `has_more`.

Lỗi trả `400` dạng `{"error": "<code>", "message": "..."}` với code:
`bad_sort`, `bad_strategy`, `bad_param`, `bad_cursor`, `cursor_mismatch`.

## Thiết kế chính

- **Sort whitelist**: chỉ cho sort theo `id/title/price/stock`, không bao giờ đưa tên cột thô vào `order_by()` (chống SQL injection).
- **Tie-break bằng id**: luôn thêm `id` vào cuối danh sách sort, nên thứ tự luôn xác định dù nhiều sách trùng giá.
- **Cursor đa khóa (keyset)**: cursor lưu giá trị các khóa sort của item cuối trang. Trang sau dùng điều kiện
  `(k1 > v1) OR (k1 = v1 AND k2 > v2) OR ...` (đổi `>` thành `<` với khóa giảm dần), nên hỗ trợ cả sort hỗn hợp tăng/giảm.
- **Cursor ràng buộc với sort + genre**: dùng cursor với sort/genre khác sẽ trả `400 cursor_mismatch`.
- **+1 trick**: lấy `limit + 1` dòng để biết còn trang sau mà không cần `COUNT`.
- **Tránh N+1**: dùng `selectinload` khi trả kèm `category` và `authors`.

## Postman

Import file `postman/bookstore.postman_collection.json`. Biến `baseUrl` mặc định `http://localhost:5000`.
Chạy theo thứ tự (hoặc Collection Runner): request 2 và 3 tự lưu `next_cursor` vào biến `{{cursor}}`
để request tiếp theo dùng.

## Cấu trúc

```
bookstore-api/
  app.py            # create_app
  models.py         # Book, Author, Category, bảng book_authors
  routes/books.py   # list_books: offset + cursor + genre + multi-key sort
  seed.py           # dữ liệu mẫu
  tests/test_books.py
  postman/bookstore.postman_collection.json
```

## Nộp bài (Git)

```bash
git init
git add .
git commit -m "Bài 2: pagination offset + cursor, filter genre, multi-key sort"
```
