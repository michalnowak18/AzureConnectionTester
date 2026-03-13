from azure.identity import WorkloadIdentityCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError, HttpResponseError

from testers.result import make_result


def test_blob(credential: WorkloadIdentityCredential, storage_account_name: str) -> dict:
    result = make_result("Azure Blob Storage", storage_account_name)
    account_url = f"https://{storage_account_name}.blob.core.windows.net"

    try:
        client = BlobServiceClient(account_url=account_url, credential=credential)
        containers = list(client.list_containers(results_per_page=5))
        result["status"] = "OK"
        result["details"] = {
            "containers_found": len(containers),
            "container_names": [c["name"] for c in containers],
        }
    except HttpResponseError as e:
        result["error"] = f"HTTP {e.status_code}: {e.reason} — {e.message}"
    except AzureError as e:
        result["error"] = f"Azure credential error: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result