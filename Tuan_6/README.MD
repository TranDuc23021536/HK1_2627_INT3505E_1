# SOA — Buổi 6: Authentication & Authorization

## Lab 1 — Basic Auth

curl.exe -k -i --ssl-no-revoke -u "an@vnu.edu.vn:correct horse battery staple" https://localhost:5001/api/orders

Kết quả mong đợi: `HTTP/1.1 200 OK`, body có `"principal":"an@vnu.edu.vn"`.

![Lab 1](images/lab1.png)



