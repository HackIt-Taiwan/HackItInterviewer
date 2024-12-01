FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN  pip install pyuwsgi

COPY . .

EXPOSE 3000

ENV PYTHONUNBUFFERED=1

CMD ["uwsgi", "--http", "0.0.0.0:3000", "--module", "run:app", "--master", "-p", "4"]