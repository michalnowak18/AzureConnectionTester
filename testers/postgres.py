import psycopg2
from azure.identity import WorkloadIdentityCredential
from azure.core.exceptions import AzureError

from testers.result import make_result

# Fixed Azure resource URI for PostgreSQL Entra authentication — do not change
POSTGRES_TOKEN_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"


def test_postgres(
    credential: WorkloadIdentityCredential,
    host: str,
    database: str,
    username: str,
    port: int = 5432,
) -> dict:
    """
    Tests connectivity to an Azure PostgreSQL Flexible Server using Entra
    (formerly AAD) authentication via Workload Identity.

    The username must match the Entra user or Managed Identity display name
    that has been added as an admin or user on the Postgres server.
    SSL is enforced — Azure Flexible Server requires it.
    """
    result = make_result("Azure PostgreSQL Flexible Server", host)

    try:
        # Step 1 — acquire a token scoped to the PostgreSQL resource.
        # The SDK exchanges the SA federated token for an Entra access token.
        token = credential.get_token(POSTGRES_TOKEN_SCOPE)

        # Step 2 — connect using the access token as the password.
        # psycopg2 treats it as a plain password field.
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=database,
            user=username,
            password=token.token,
            sslmode="require",  # mandatory for Azure Flexible Server
            connect_timeout=10,
        )

        # Step 3 — run a minimal query to confirm the session is live.
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

        conn.close()

        result["status"] = "OK"
        result["details"] = {
            "host": host,
            "database": database,
            "postgres_version": version,
        }

    except AzureError as e:
        # Token acquisition failed — FIC/SA/MI misconfiguration
        result["error"] = f"Azure credential error: {str(e)}"
    except psycopg2.OperationalError as e:
        # Covers: wrong host, SSL issues, network blocked, wrong username
        result["error"] = f"Connection error: {str(e).strip()}"
    except psycopg2.Error as e:
        # Covers: auth rejected, wrong DB name, permission denied
        result["error"] = f"Database error: {str(e).strip()}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result