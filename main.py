from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure.identity import WorkloadIdentityCredential
from azure.core.exceptions import AzureError
import os

from testers import test_blob, test_keyvault, test_postgres, test_acr, test_ado_pipeline
from request_dto import BlobRequest, KeyVaultRequest, PostgresRequest, AcrRequest, AdoPipelineRequest


# --- Credential is created once at startup and reused across all requests.
# The SDK handles token caching and refresh internally.
credential: Optional[WorkloadIdentityCredential] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global credential
    try:
        credential = WorkloadIdentityCredential()
    except Exception as e:
        # Fail fast at startup if credential cannot be initialised
        raise RuntimeError(f"Failed to initialise WorkloadIdentityCredential: {e}")
    yield
    # Nothing to clean up — credential holds no persistent connections


app = FastAPI(
    title="Azure Connectivity Tester",
    description="Tests connectivity and authentication to Azure resources using Workload Identity.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Health check ---

@app.get("/healthz")
def health():
    return {"status": "ok"}


# --- Test endpoints ---

@app.post("/test/blob")
def test_blob_endpoint(request: BlobRequest):
    result = test_blob(credential, request.storage_account_name)
    if result["status"] == "FAIL":
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@app.post("/test/keyvault")
def test_keyvault_endpoint(request: KeyVaultRequest):
    result = test_keyvault(credential, request.keyvault_name)
    if result["status"] == "FAIL":
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@app.post("/test/postgres")
def test_postgres_endpoint(request: PostgresRequest):
    result = test_postgres(credential, request.host, request.database, request.username, request.port)
    if result["status"] == "FAIL":
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@app.post("/test/acr")
def test_acr_endpoint(request: AcrRequest):
    tenant_id = request.tenant_id or os.getenv("AZURE_TENANT_ID")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required either in the request body or as AZURE_TENANT_ID env var.")
    result = test_acr(credential, request.registry_name, tenant_id)
    if result["status"] == "FAIL":
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@app.post("/trigger/pipeline")
def trigger_pipeline_endpoint(request: AdoPipelineRequest):
    result = test_ado_pipeline(
        credential,
        request.organization,
        request.project,
        request.pipeline_id,
        request.branch,
        request.parameters,
    )
    if result["status"] == "FAIL":
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@app.post("/test/all")
def test_all_endpoint(
    blob: Optional[BlobRequest] = None,
    keyvault: Optional[KeyVaultRequest] = None,
    postgres: Optional[PostgresRequest] = None,
    acr: Optional[AcrRequest] = None,
):
    if not any([blob, keyvault, postgres, acr]):
        raise HTTPException(status_code=400, detail="At least one resource must be specified.")

    results = []
    if blob:
        results.append(test_blob(credential, blob.storage_account_name))
    if keyvault:
        results.append(test_keyvault(credential, keyvault.keyvault_name))
    if postgres:
        results.append(test_postgres(credential, postgres.host, postgres.database, postgres.username, postgres.port))
    if acr:
        tenant_id = acr.tenant_id or os.getenv("AZURE_TENANT_ID")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id is required for ACR test.")
        results.append(test_acr(credential, acr.registry_name, tenant_id))

    failed = [r for r in results if r["status"] == "FAIL"]
    return {
        "summary": "All tests passed." if not failed else f"{len(failed)} test(s) failed.",
        "results": results,
    }