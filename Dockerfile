FROM python:3.11-slim

# Tắt prompt, tăng tốc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cài gói hệ thống (nếu cần psycopg2)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy file requirements
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source
COPY . /app/

# Expose port cho gunicorn
EXPOSE 8000

# Lệnh chạy mặc định (override trong compose cũng được)
CMD ["gunicorn", "thabicare_admin.wsgi:application", "--bind", "0.0.0.0:8000"]
