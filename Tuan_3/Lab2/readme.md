Test 1: Resource không tồn tại
lệnh: curl.exe -i -H "Accept: application/json" http://localhost:5000/resources/999
Kỳ vọng: HTTP 404, Content-Type: application/problem+json, body có type/title/detail/status/instance
kết quả: ![alt text](<Screenshot 2026-10-06 103626.png>)

Test 2: Client gửi Accept: application/json
lệnh: curl.exe -i -H "Accept: application/json" http://localhost:5000/resources/999
kỳ vọng: Kỳ vọng: vẫn trả problem+json
kết quả: ![alt text](<Screenshot 2026-10-06 103840.png>)

Test 3: Không gửi header Accept
lệnh: curl.exe -i -H "Accept:" http://localhost:5000/resources/999
kỳ vọng: vẫn trả problem+json
kết quả: ![alt text](<Screenshot 2026-10-06 104034.png>)

Test 4: Endpoint không tồn tại (fallback HTTPException)
lệnh: curl.exe -i http://localhost:5000/duc
kỳ vọng: 404 dạng problem+json, không phải trang HTML mặc định của Flask
kết quả: ![alt text](<Screenshot 2026-10-06 104252.png>)

test 5: Exception chưa được bắt
lệnh: curl.exe -i http://localhost:5000/test-500
Kỳ vọng: HTTP 500, message trung tính, không lộ stack trace hay nội dung exception
kết quả: ![alt text](<Screenshot 2026-10-06 104443.png>)