"""
Load Synthea-generated FHIR R4 Transaction Bundles into HAPI FHIR server.

Usage:
    1. Download Synthea: https://github.com/synthetichealth/synthea/releases
    2. Generate patients: java -jar synthea-with-dependencies.jar -p 100
    3. Run this script: python load_patients.py --fhir-dir ./output/fhir
"""

import argparse
import json
import sys
from pathlib import Path

import httpx


def load_bundles(fhir_dir: str, server_url: str) -> None:
    fhir_path = Path(fhir_dir)
    if not fhir_path.exists():
        print(f"Directory not found: {fhir_dir}")
        sys.exit(1)

    bundle_files = sorted(fhir_path.glob("*.json"))
    if not bundle_files:
        print(f"No JSON files found in {fhir_dir}")
        sys.exit(1)

    client = httpx.Client(timeout=30.0)
    loaded = 0
    errors = 0

    for bundle_file in bundle_files:
        try:
            bundle = json.loads(bundle_file.read_text(encoding="utf-8"))
            if bundle.get("resourceType") != "Bundle":
                continue

            resp = client.post(
                server_url,
                json=bundle,
                headers={"Content-Type": "application/fhir+json"},
            )
            if resp.status_code in (200, 201):
                loaded += 1
                print(f"  Loaded: {bundle_file.name}")
            else:
                errors += 1
                print(f"  FAILED ({resp.status_code}): {bundle_file.name}")
        except Exception as e:
            errors += 1
            print(f"  ERROR: {bundle_file.name} — {e}")

    print(f"\nDone. Loaded {loaded} bundles, {errors} errors.")
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Synthea bundles into HAPI FHIR")
    parser.add_argument(
        "--fhir-dir",
        default="./output/fhir",
        help="Directory containing Synthea FHIR JSON bundles",
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:8080/fhir",
        help="HAPI FHIR server base URL",
    )
    args = parser.parse_args()
    load_bundles(args.fhir_dir, args.server_url)
