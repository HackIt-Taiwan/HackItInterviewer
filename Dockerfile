FROM python:3.12-slim

COPY /app /app
COPY run.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80
ENV PYTHONUNBUFFERED=1

CMD ["python", "run.py"]
