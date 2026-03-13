import os
import sys
from azure.identity import WorkloadIdentityCredential

from testers import test_blob, test_keyvault


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

    if not storage_account_name and not keyvault_name:
        print("ERROR: At least one of AZURE_STORAGE_ACCOUNT_NAME or AZURE_KEYVAULT_NAME must be set.")
        sys.exit(1)

    credential = get_credential()

    tests = []
    if storage_account_name:
        tests.append(test_blob(credential, storage_account_name))
    if keyvault_name:
        tests.append(test_keyvault(credential, keyvault_name))

    print("\n=== Azure Connectivity Test Results ===")
    for result in tests:
        print_result(result)

    failed = [r for r in tests if r["status"] == "FAIL"]
    print(f"\n{'All tests passed.' if not failed else f'{len(failed)} test(s) failed.'}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()