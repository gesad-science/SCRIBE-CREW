FROM python:3.11-slim

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia dependências
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia apenas o que o container precisa
COPY src ./src
COPY pdfs ./pdfs
COPY plans ./plans
COPY tests ./tests
COPY config.yaml .
COPY main.py .
COPY .env .

# Expõe a porta da aplicação
EXPOSE 8000

# Comando que inicia o container
CMD ["python", "main.py"]
