from azure.identity import WorkloadIdentityCredential
from azure.keyvault.secrets import SecretClient
from azure.core.exceptions import AzureError, HttpResponseError

from testers.result import make_result


def test_keyvault(credential: WorkloadIdentityCredential, keyvault_name: str) -> dict:
    result = make_result("Azure Key Vault", keyvault_name)
    vault_url = f"https://{keyvault_name}.vault.azure.net"

    try:
        client = SecretClient(vault_url=vault_url, credential=credential)
        secrets = list(client.list_properties_of_secrets(max_page_size=5))
        result["status"] = "OK"
        result["details"] = {
            "secrets_found": len(secrets),
            "secret_names": [s.name for s in secrets],
        }
    except HttpResponseError as e:
        result["error"] = f"HTTP {e.status_code}: {e.reason} — {e.message}"
    except AzureError as e:
        result["error"] = f"Azure credential error: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result