lệnh 1: curl.exe "http://localhost:5000/orders?status=paid"
mục đính: filter theo status
kỳ vọng: Mọi đơn có status = paid
kết quả: ![alt text](<Screenshot 2026-10-06 110745.png>)

lệnh 2: curl.exe "http://localhost:5000/orders?limit=5"
mục đích: Giới hạn số bản ghi
kỳ vọng: Đúng 5 bản ghi, có next_cursor
kết quả: ![alt text](<Screenshot 2026-10-06 111404.png>)

lệnh 3: curl.exe "http://localhost:5000/orders?fields=id,total"
mục đích: Sparse fieldsets
kỳ vọng: Mỗi bản ghi chỉ có id, total
kết quả: ![alt text](<Screenshot 2026-10-06 111554.png>)

lệnh 4: curl.exe "http://localhost:5000/orders?customer_id=3&sort=-total&limit=3"
mục đích: Kết hợp filter + sort
kỳ vọng: Chỉ đơn của khách 3, total giảm dần
kết quả:![alt text](<Screenshot 2026-10-06 111836.png>)

lệnh 5: curl.exe -i "http://localhost:5000/orders?cursor=abc123"
mục đích: cursor hỏng
kỳ vọng: 400, problem+json, type kết thúc bằng invalid-cursor
kết quả: ![alt text](<Screenshot 2026-10-06 111950.png>)

lệnh 6: curl.exe -i "http://localhost:5000/orders?limit=1000"
mục đích: Tham số sai
kỳ vọng: 400 cho cả hai
kết quả: ![alt text](<Screenshot 2026-10-06 112241.png>)

lệnh 7: pytest -q
test tự động, tất cả các test đều pass
![alt text](<Screenshot 2026-10-06 112404.png>)