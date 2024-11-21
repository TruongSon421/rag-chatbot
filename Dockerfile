# Sử dụng image Python chính thức nhẹ
FROM python:3.11

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào container và cài đặt các phụ thuộc
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Sao chép toàn bộ mã nguồn vào thư mục làm việc trong container
COPY . /app/

# Chạy các lệnh Python sau khi container được khởi động
# Docker Compose đã chỉ định các lệnh python trong `command`, không cần thêm CMD ở đây
