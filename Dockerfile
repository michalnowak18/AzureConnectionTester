FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/packages -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/packages /app/packages
COPY main.py .
COPY testers/ testers/

ENV PYTHONPATH=/app/packages
ENV AZURE_CLIENT_ID=""
ENV AZURE_TENANT_ID=""
ENV AZURE_FEDERATED_TOKEN_FILE=""
ENV AZURE_STORAGE_ACCOUNT_NAME=""
ENV AZURE_KEYVAULT_NAME=""
ENV AZURE_POSTGRES_HOST=""
ENV AZURE_POSTGRES_DB=""
ENV AZURE_POSTGRES_USER=""

CMD ["python", "main.py"]