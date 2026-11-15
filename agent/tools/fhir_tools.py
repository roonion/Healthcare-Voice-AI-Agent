"""
FHIR server interaction tools — read/write HAPI FHIR resources.

These are exposed as @function_tool for agents to look up existing patient
records and write completed intake bundles.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("fhir-tools")

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL", "http://localhost:8080/fhir")


async def search_patient(
    name: str = "", phone: str = "", dob: str = ""
) -> list[dict]:
    """Search HAPI FHIR for existing patient records."""
    params = {}
    if name:
        params["name"] = name
    if phone:
        params["telecom"] = phone
    if dob:
        params["birthdate"] = dob

    if not params:
        return []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{FHIR_SERVER_URL}/Patient",
                params=params,
                headers={"Accept": "application/fhir+json"},
                timeout=10.0,
            )
            resp.raise_for_status()
            bundle = resp.json()

        entries = bundle.get("entry", [])
        results = []
        for entry in entries:
            resource = entry.get("resource", {})
            results.append({
                "id": resource.get("id"),
                "name": _format_name(resource.get("name", [{}])[0]),
                "birthDate": resource.get("birthDate"),
                "phone": _extract_telecom(resource, "phone"),
            })
        return results

    except Exception:
        logger.exception("FHIR patient search failed")
        return []


async def get_patient_allergies(patient_id: str) -> list[dict]:
    """Retrieve allergy records for a patient."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{FHIR_SERVER_URL}/AllergyIntolerance",
                params={"patient": patient_id},
                headers={"Accept": "application/fhir+json"},
                timeout=10.0,
            )
            resp.raise_for_status()
            bundle = resp.json()

        return [
            {
                "substance": (
                    entry.get("resource", {}).get("code", {}).get("text", "Unknown")
                ),
                "reactions": [
                    r.get("description", "")
                    for r in entry.get("resource", {}).get("reaction", [])
                ],
            }
            for entry in bundle.get("entry", [])
        ]

    except Exception:
        logger.exception("FHIR allergy lookup failed")
        return []


async def get_patient_medications(patient_id: str) -> list[dict]:
    """Retrieve active medications for a patient."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{FHIR_SERVER_URL}/MedicationStatement",
                params={"patient": patient_id, "status": "active"},
                headers={"Accept": "application/fhir+json"},
                timeout=10.0,
            )
            resp.raise_for_status()
            bundle = resp.json()

        return [
            {
                "name": (
                    entry.get("resource", {})
                    .get("medicationCodeableConcept", {})
                    .get("text", "Unknown")
                ),
                "dosage": (
                    entry.get("resource", {}).get("dosage", [{}])[0].get("text", "")
                ),
            }
            for entry in bundle.get("entry", [])
        ]

    except Exception:
        logger.exception("FHIR medication lookup failed")
        return []


async def post_bundle(transaction_bundle: dict) -> str | None:
    """POST a FHIR Transaction Bundle to the server. Returns bundle ID or None."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                FHIR_SERVER_URL,
                json=transaction_bundle,
                headers={"Content-Type": "application/fhir+json"},
                timeout=15.0,
            )
            if resp.status_code in (200, 201):
                result = resp.json()
                bundle_id = result.get("id", "")
                logger.info("Bundle posted: id=%s", bundle_id)
                return bundle_id
            else:
                logger.error("Bundle POST failed: %d", resp.status_code)
                return None

    except Exception:
        logger.exception("FHIR bundle POST failed")
        return None


def _format_name(name_obj: dict) -> str:
    given = " ".join(name_obj.get("given", []))
    family = name_obj.get("family", "")
    return f"{given} {family}".strip()


def _extract_telecom(resource: dict, system: str) -> str:
    for telecom in resource.get("telecom", []):
        if telecom.get("system") == system:
            return telecom.get("value", "")
    return ""
