import os
import sys
from azure.identity import WorkloadIdentityCredential

from testers import test_blob, test_keyvault, test_postgres


def get_credential() -> WorkloadIdentityCredential:
    return WorkloadIdentityCredential()


def print_result(result: dict) -> None:
    symbol = "✅" if result["status"] == "OK" else "❌"
    print(f"\n{symbol} [{result['status']}] {result['resource']} — {result['identifier']}")

    if result["details"]:
        for key, value in result["details"].items():
            if isinstance(value, list):
                print(f"   {key}: {len(value)}")
                for item in value:
                    print(f"     • {item}")
            else:
                print(f"   {key}: {value}")

    if result["error"]:
        print(f"   Error: {result['error']}")


def main() -> None:
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    keyvault_name = os.getenv("AZURE_KEYVAULT_NAME")
    postgres_host = os.getenv("AZURE_POSTGRES_HOST")
    postgres_db = os.getenv("AZURE_POSTGRES_DB")
    postgres_user = os.getenv("AZURE_POSTGRES_USER")

    if not any([storage_account_name, keyvault_name, postgres_host]):
        print("ERROR: At least one of the variables must be set.")
        sys.exit(1)

    credential = get_credential()

    tests = []
    if storage_account_name:
        tests.append(test_blob(credential, storage_account_name))
    if keyvault_name:
        tests.append(test_keyvault(credential, keyvault_name))
    if postgres_host:
        if not postgres_db or not postgres_user:
            print("ERROR: AZURE_POSTGRES_DB and AZURE_POSTGRES_USER are required when AZURE_POSTGRES_HOST is set.")
            sys.exit(1)
        tests.append(test_postgres(credential, postgres_host, postgres_db, postgres_user))

    print("\n=== Azure Connectivity Test Results ===")
    for result in tests:
        print_result(result)

    failed = [r for r in tests if r["status"] == "FAIL"]
    print(f"\n{'All tests passed.' if not failed else f'{len(failed)} test(s) failed.'}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()