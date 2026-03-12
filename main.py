import os
import sys
from azure.identity import DefaultAzureCredential, WorkloadIdentityCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError, HttpResponseError

def test_blob_connectivity(storage_account_name: str) -> dict:
    result = {
        "resource": "Azure Blob Storage",
        "account": storage_account_name,
        "status": "FAIL",
        "details": None,
        "error": None,
    }

    account_url = f"https://{storage_account_name}.blob.core.windows.net"

    try:
        # Reads AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_FEDERATED_TOKEN_FILE
        # which are injected automatically by the AZWI mutating webhook.
        credential = WorkloadIdentityCredential()

        client = BlobServiceClient(account_url=account_url, credential=credential)

        # Actual connectivity test: list containers (requires at minimum
        # Storage Blob Data Reader on the storage account scope).
        containers = list(client.list_containers(results_per_page=5))

        result["status"] = "OK"
        result["details"] = {
            "containers_found": len(containers),
            "container_names": [c["name"] for c in containers],
        }

    except HttpResponseError as e:
        # Covers 403 Forbidden (wrong RBAC), 404 (wrong account name), etc.
        result["error"] = f"HTTP {e.status_code}: {e.reason} — {e.message}"

    except AzureError as e:
        # Covers credential/token exchange failures (misconfigured FIC, wrong
        # client ID annotation on the SA, token file not mounted, etc.)
        result["error"] = f"Azure credential error: {str(e)}"

    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result

if __name__ == "__main__":
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")

    if not storage_account:
        print("ERROR: AZURE_STORAGE_ACCOUNT_NAME environment variable not set.")
        sys.exit(1)

    test_result = test_blob_connectivity(storage_account)

    status_symbol = "✅" if test_result["status"] == "OK" else "❌"
    print(f"\n{status_symbol} [{test_result['status']}] {test_result['resource']} — {test_result['account']}")

    if test_result["details"]:
        print(f"   Containers visible: {test_result['details']['containers_found']}")
        for name in test_result["details"]["container_names"]:
            print(f"     • {name}")

    if test_result["error"]:
        print(f"   Error: {test_result['error']}")

