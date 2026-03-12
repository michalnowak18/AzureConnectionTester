# --- Stage 1: builder ---
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/packages -r requirements.txt

# --- Stage 2: runtime ---
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /app/packages /app/packages
COPY main.py .

# Tell Python where to find the installed packages
ENV PYTHONPATH=/app/packages

# AZWI env vars — these will be injected by the webhook at runtime,
# but defining them here documents what the pod expects
ENV AZURE_CLIENT_ID=""
ENV AZURE_TENANT_ID=""
ENV AZURE_FEDERATED_TOKEN_FILE=""
ENV AZURE_STORAGE_ACCOUNT_NAME=""

CMD ["python", "main.py"]