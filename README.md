🔐 SecureShare – Secure File Sharing Application (PKI Enabled)

SecureShare is a cryptography-focused secure file sharing system that uses PKI, RSA, AES (Fernet), digital signatures, and Dockerized deployment.
It provides a secure backend API and a cross-platform desktop GUI client (Windows & Linux).

This guide explains how to run the full application using Docker images pulled from GitHub Container Registry (GHCR).

🔐 SecureShare – Secure File Sharing Application (PKI Enabled)

SecureShare is a cryptography-focused secure file sharing system that uses PKI, RSA, AES (Fernet), digital signatures, and Dockerized deployment.
It provides a secure backend API and a cross-platform desktop GUI client (Windows & Linux).

This guide explains how to run the full application using Docker images pulled from GitHub Container Registry (GHCR).

Prerequisites

Make sure you have the following installed:

Docker (v20+)

Docker Compose v2

Internet access (to pull images)

(MUST HAVE)
docker-compose.yml:

services:
  db:
    image: postgres:15-alpine
    container_name: cryptoshare-db
    environment:
      POSTGRES_USER: cow
      POSTGRES_PASSWORD: cow123
      POSTGRES_DB: cryptoshare
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cow"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    image: ghcr.io/<YOUR_GITHUB_USERNAME>/cryptoshare-backend:latest
    container_name: cryptoshare-backend
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://cow:cow123@db:5432/cryptoshare
      SECRET_KEY: change_this_to_a_long_random_secret
      CA_KEY_PATH: /app/pki/ca.key
      CA_CERT_PATH: /app/pki/ca.crt
    ports:
      - "8000:8000"
    restart: unless-stopped

volumes:
  db_data:


pull the backend and database from package:

docker pull ghcr.io/rajan-mgr/cryptoshare-backend:v1.0.26

after docker pull run:
(!IMPP)
docker compose run --rm backend python setup_ca.py

after these steps:

docker compose up -d (same folder where docker-compose.yml is)

can download the app from release:

There are gui app for windows and linux also can use source code.

running from source code:

cd gui
python app.py




