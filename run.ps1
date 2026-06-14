# Chạy backend từ thư mục gốc D:\Code\DA
# Lệnh đúng: uvicorn backend.app.main:app  (không phải app.main:app)
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
