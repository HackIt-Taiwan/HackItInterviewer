FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir uwsgi

COPY . .

EXPOSE 3000

ENV PYTHONUNBUFFERED=1

# 使用 uWSGI 運行應用
CMD ["uwsgi", "--http", "0.0.0.0:3000", "--module", "run:app", "--master", "--processes", "4", "--threads", "2"]