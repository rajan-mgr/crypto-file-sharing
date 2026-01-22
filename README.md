# 🔐 SecureShare - PKI-Enabled Secure File Sharing

A cryptography-focused secure file sharing system leveraging Public Key Infrastructure (PKI), RSA encryption, AES (Fernet) symmetric encryption, and digital signatures. SecureShare provides a robust backend API with a cross-platform desktop GUI client supporting Windows and Linux.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
  - [Quick Start with Docker](#quick-start-with-docker)
  - [Running from Source](#running-from-source)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Security Considerations](#-security-considerations)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

- **Public Key Infrastructure (PKI)** - Certificate-based authentication and trust management
- **Hybrid Encryption** - RSA for key exchange, AES (Fernet) for file encryption
- **Digital Signatures** - Cryptographic verification of file integrity and authenticity
- **Dockerized Deployment** - Easy setup and deployment using Docker containers
- **Cross-Platform GUI** - Desktop client for Windows and Linux
- **PostgreSQL Backend** - Reliable data persistence and user management

---

## 🏗 Architecture

SecureShare consists of three main components:

1. **PostgreSQL Database** - Stores user credentials, file metadata, and certificates
2. **Backend API** - FastAPI-based REST API handling authentication, encryption, and file operations
3. **GUI Client** - Python-based desktop application for user interaction

---

## 📦 Prerequisites

Before installing SecureShare, ensure you have:

- **Docker** (v20.0 or higher) - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (v2.0 or higher) - [Install Docker Compose](https://docs.docker.com/compose/install/)
- **Internet Connection** - Required for pulling Docker images
- **Python 3.8+** (only if running GUI from source)

---

## 🚀 Installation

### Quick Start with Docker

#### Step 1: Create Docker Compose Configuration

Create a new directory for SecureShare and create a `docker-compose.yml` file:

```yaml
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
    image: ghcr.io/rajan-mgr/cryptoshare-backend:v1.0.26
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
```

#### Step 2: Pull Backend Image

```bash
docker pull ghcr.io/rajan-mgr/cryptoshare-backend:v1.0.26
```

#### Step 3: Initialize PKI Certificate Authority

**⚠️ CRITICAL STEP** - This must be run before starting the services:

```bash
docker compose run --rm backend python setup_ca.py
```

This command generates the Certificate Authority (CA) keys and certificates required for PKI operations.

#### Step 4: Start Services

```bash
docker compose up -d
```

The backend API will be accessible at `http://localhost:8000`

#### Step 5: Verify Deployment

Check that all services are running:

```bash
docker compose ps
```

You should see both `cryptoshare-db` and `cryptoshare-backend` with status "Up".

---

### Running from Source

If you prefer to run the GUI client from source code:

#### Step 1: Clone Repository

```bash
git clone https://github.com/rajan-mgr/cryptoshare.git
cd cryptoshare
```

#### Step 2: Install Dependencies

```bash
cd gui
pip install -r requirements.txt
```

#### Step 3: Launch GUI Application

```bash
python app.py
```

---

## 💻 Usage

### Using Pre-built GUI Clients

Download the appropriate client for your operating system from the [Releases](https://github.com/rajan-mgr/cryptoshare/releases) page:

- **Windows**: `SecureShare-Windows.exe`
- **Linux**: `SecureShare-Linux` (may require `chmod +x` to make executable)

### First-Time Setup

1. Launch the GUI application
2. The application will connect to `http://localhost:8000` by default
3. Register a new account or log in with existing credentials
4. Your PKI certificates will be automatically generated upon first login

### Sharing Files

1. Click "Upload File" and select the file you wish to share
2. The file will be encrypted using hybrid encryption (RSA + AES)
3. Share the file link or identifier with intended recipients
4. Recipients can download and decrypt files using their private keys


## 🔧 Troubleshooting

### Backend Won't Start

**Problem**: Backend container exits immediately

**Solution**: Ensure CA setup was completed:
```bash
docker compose run --rm backend python setup_ca.py
docker compose up -d
```

### Database Connection Issues

**Problem**: Backend cannot connect to database

**Solution**: Check database health status:
```bash
docker compose logs db
docker compose ps
```

Wait for the database health check to pass before starting the backend.

### GUI Cannot Connect

**Problem**: GUI client shows connection error

**Solution**: 
1. Verify backend is running: `docker compose ps`
2. Check backend logs: `docker compose logs backend`
3. Ensure firewall allows connections on port 8000
4. Try accessing `http://localhost:8000/docs` in a web browser

### Port Already in Use

**Problem**: Port 8000 or 5432 already occupied

**Solution**: Either stop the conflicting service or change ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Maps host port 8001 to container port 8000
```

---

## 🔒 Security Considerations

- **Certificate Storage**: Private keys are stored locally on each client. Never share your private key.
- **Transport Security**: Consider using HTTPS/TLS in production by placing a reverse proxy (nginx, Caddy) in front of the backend.
- **Secret Management**: Rotate `SECRET_KEY` regularly and use environment-specific secrets.
- **Database Security**: Use strong passwords and restrict database access in production.
- **Backup**: Regularly backup the PostgreSQL volume containing user data and certificates.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📞 Support

For issues, questions, or feature requests, please:

- Open an issue on [GitHub Issues](https://github.com/rajan-mgr/cryptoshare/issues)
- Check existing documentation in the `/docs` folder
- Review closed issues for similar problems

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Cryptography library for Python cryptographic primitives
- PostgreSQL team for the robust database system
- Docker for containerization technology

---

**Made with 🔐 by the SecureShare Team**