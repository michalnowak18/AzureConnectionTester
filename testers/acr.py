import requests
from azure.identity import WorkloadIdentityCredential
from azure.core.exceptions import AzureError

from testers.result import make_result

# Fixed Azure resource URI for ACR token exchange — do not change
ACR_TOKEN_SCOPE = "https://management.azure.com/.default"


def _exchange_acr_refresh_token(
    registry_host: str,
    entra_token: str,
    tenant_id: str,
) -> str:
    """
    Exchanges an Entra access token for an ACR refresh token.
    This is ACR's OAuth exchange endpoint — specific to Azure Container Registry.
    """
    url = f"https://{registry_host}/oauth2/exchange"
    response = requests.post(url, data={
        "grant_type": "access_token",
        "service": registry_host,
        "tenant": tenant_id,
        "access_token": entra_token,
    }, timeout=10)

    response.raise_for_status()
    return response.json()["refresh_token"]


def _get_acr_access_token(
    registry_host: str,
    refresh_token: str,
    scope: str = "registry:catalog:*",
) -> str:
    """
    Exchanges an ACR refresh token for a short-lived ACR access token
    scoped to a specific registry action.
    """
    url = f"https://{registry_host}/oauth2/token"
    response = requests.post(url, data={
        "grant_type": "refresh_token",
        "service": registry_host,
        "scope": scope,
        "refresh_token": refresh_token,
    }, timeout=10)

    response.raise_for_status()
    return response.json()["access_token"]


def test_acr(
    credential: WorkloadIdentityCredential,
    registry_name: str,
    tenant_id: str,
) -> dict:
    """
    Tests connectivity and authentication to an Azure Container Registry
    using Workload Identity.

    The Managed Identity needs AcrPull (or higher) role on the registry.
    Tests by listing repositories via the catalog API.
    """
    registry_host = f"{registry_name}.azurecr.io"
    result = make_result("Azure Container Registry", registry_host)

    try:
        # Step 1 — get an Entra access token scoped to Azure management
        entra_token = credential.get_token(ACR_TOKEN_SCOPE).token

        # Step 2 — exchange it for an ACR-specific refresh token
        refresh_token = _exchange_acr_refresh_token(registry_host, entra_token, tenant_id)

        # Step 3 — get a short-lived ACR access token for catalog access
        access_token = _get_acr_access_token(registry_host, refresh_token)

        # Step 4 — call the catalog API to list repositories
        catalog_url = f"https://{registry_host}/v2/_catalog"
        response = requests.get(
            catalog_url,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"last": "", "n": 5},
            timeout=10,
        )
        response.raise_for_status()

        repositories = response.json().get("repositories") or []
        result["status"] = "OK"
        result["details"] = {
            "registry": registry_host,
            "repositories_found": len(repositories),
            "repository_names": repositories,
        }

    except AzureError as e:
        result["error"] = f"Azure credential error: {str(e)}"
    except requests.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code}: {e.response.reason} — {e.response.text.strip()}"
    except requests.ConnectionError as e:
        result["error"] = f"Connection error: {str(e)}"
    except requests.Timeout:
        result["error"] = "Request timed out"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result