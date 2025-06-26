# Dockerfile
FROM python:3.10-slim

# 필수 시스템 패키지 설치 (PostgreSQL 드라이버 등)
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 개발용 커맨드: 마이그레이션 후 개발 서버 실행
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]