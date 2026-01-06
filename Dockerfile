
FROM python:3.12-slim

# Install system dependencies for Tkinter GUI
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-tk \
        tk \
        tcl8.6 \
        build-essential \
        libffi-dev \
        libssl-dev \
        wget \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /securefile-app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
