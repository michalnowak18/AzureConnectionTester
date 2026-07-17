FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/packages -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/packages /app/packages
COPY main.py .
COPY request_dto.py .
COPY testers/ testers/

ENV PYTHONPATH=/app/packages
ENV AZURE_CLIENT_ID=""
ENV AZURE_TENANT_ID=""
ENV AZURE_FEDERATED_TOKEN_FILE=""

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]