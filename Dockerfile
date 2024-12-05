FROM python:3.12-slim

RUN apt-get update && apt-get install -y libexpat1 libexpat1-dev python3-dev build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY /app /app
COPY run.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000

ENV PYTHONUNBUFFERED=1

RUN echo "source activate my_env" > ~/.bashrc

ENV PATH /opt/conda/envs/my_env/bin:$PATH

CMD ["python", "run.py"]
