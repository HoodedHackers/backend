FROM python:3.13-slim-bookworm

WORKDIR /app

RUN python3 -m venv .venv
COPY requirements.txt .
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 80
ENV DB_PATH="sqlite:///./local.db"

CMD ["./.venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
