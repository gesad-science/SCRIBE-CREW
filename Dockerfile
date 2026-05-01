FROM python:3.11-slim

WORKDIR /app

# Instala supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código
COPY src ./src
# COPY pdfs ./pdfs
COPY plans ./plans
COPY tests ./tests
COPY config.yaml .
COPY main.py .
COPY .env .

# Copia seus scripts A2A (se estiverem em src)
# Eles já estão sendo copiados com COPY src ./src

# Copia configuração do supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expõe todas as portas
EXPOSE 8000 9994 9995 9996 9997 9998

# Roda supervisor (que gerencia todos os serviços)
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
