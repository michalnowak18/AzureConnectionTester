from pydantic import BaseModel

class BlobRequest(BaseModel):
    storage_account_name: str

class KeyVaultRequest(BaseModel):
    keyvault_name: str

class PostgresRequest(BaseModel):
    host: str
    database: str
    username: str
    port: int = 5432

class AcrRequest(BaseModel):
    registry_name: str
    tenant_id: str = None   # falls back to AZURE_TENANT_ID env var if not provided

class AdoPipelineRequest(BaseModel):
    organization: str
    project: str
    pipeline_id: int
    branch: str = "main"
    parameters: dict = {}