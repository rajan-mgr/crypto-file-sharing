FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    tk \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install  -r requirements.txt

COPY . .

# Do NOT bake secrets here
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
