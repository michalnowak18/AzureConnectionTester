import requests
from azure.identity import WorkloadIdentityCredential
from azure.core.exceptions import AzureError

from testers.result import make_result

# Azure DevOps resource URI for token scoping
ADO_TOKEN_SCOPE = "499b84ac-1321-427f-aa17-267ca6975798/.default"
ADO_API_VERSION = "7.1"


def test_ado_pipeline(
    credential: WorkloadIdentityCredential,
    organization: str,
    project: str,
    pipeline_id: int,
    branch: str = "main",
    parameters: dict = None,
) -> dict:
    """
    Triggers an Azure DevOps pipeline using Workload Identity.

    The Managed Identity must be added as a user in the ADO project
    with 'Build (Read & execute)' permission on the target pipeline.
    """
    result = make_result("Azure DevOps Pipeline", f"{organization}/{project}/pipeline/{pipeline_id}")

    try:
        # Step 1 — acquire a token scoped to Azure DevOps
        token = credential.get_token(ADO_TOKEN_SCOPE).token

        # Step 2 — call the ADO Pipelines REST API to trigger a run
        url = (
            f"https://dev.azure.com/{organization}/{project}"
            f"/_apis/pipelines/{pipeline_id}/runs"
            f"?api-version={ADO_API_VERSION}"
        )

        payload = {
            "resources": {
                "repositories": {
                    "self": {
                        "refName": f"refs/heads/{branch}"
                    }
                }
            }
        }

        if parameters:
            payload["templateParameters"] = parameters

        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()

        run = response.json()
        result["status"] = "OK"
        result["details"] = {
            "run_id": run.get("id"),
            "run_name": run.get("name"),
            "pipeline_id": pipeline_id,
            "branch": branch,
            "state": run.get("state"),
            "url": run.get("_links", {}).get("web", {}).get("href"),
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