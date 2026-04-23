FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY pdfs ./pdfs
COPY plans ./plans
COPY tests ./tests
COPY config.yaml .
COPY main.py .
COPY .env .

EXPOSE 8000

CMD ["python", "main.py"]
