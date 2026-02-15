FROM python:3.11-slim

# Instala o unrar no sistema
RUN apt-get update && \
    apt-get install -y unrar-free && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia requirements primeiro
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto
COPY . .

EXPOSE 10000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]