"""Fetch a small public metadata sample; no API key, paid service or app DB writes."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from backend.reference_data import combine_references


def main():
    sources = []

    def fetch(endpoint, search, limit):
        url = (
            "https://api.fda.gov/device/"
            + endpoint
            + ".json?"
            + urlencode({"search": search, "limit": limit})
        )
        with urlopen(url, timeout=20) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Reference response exceeds 2 MB")
        data = json.loads(raw)
        sources.append(
            dict(
                url=url,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                last_updated=data.get("meta", {}).get("last_updated"),
                response_sha256=hashlib.sha256(raw).hexdigest(),
                license_url="https://open.fda.gov/license/",
                terms_url="https://open.fda.gov/terms/",
            )
        )
        return [{**record, "_source": sources[-1]} for record in data["results"]]

    devices = []
    for term in ["infusion", "cardiac", "monitor"]:
        devices.extend(fetch("udi", "device_description:" + term, 2))
    codes = sorted(
        {
            p["code"]
            for d in devices
            for p in d.get("product_codes", [])
            if p.get("code")
        }
    )
    classifications = []
    for code in codes:
        classifications.extend(fetch("classification", "product_code:" + code, 2))
    result = combine_references(devices, classifications)
    result.update(
        schema_version=1,
        sources=sources,
        scope="Read-only public reference sample. All application demonstrations and mutation cases remain synthetic.",
        join_key="UDI product_codes[].code == classification.product_code; category join only",
        excluded_fields=[
            "customer_contacts",
            "company_name",
            "gmdn_terms",
            "device_description",
            "free-text narratives",
            "approved warnings",
        ],
        data_rights="openFDA CC0 except third-party exclusions. GMDN content is excluded; no endorsement implied.",
    )
    out = Path("data/reference")
    out.mkdir(parents=True, exist_ok=True)
    (out / "openfda-device-reference.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    with (out / "openfda-device-reference.csv").open("w", newline="") as f:
        fields = [
            "udi_record_id",
            "udi_public_version",
            "brand_name",
            "model_number",
            "product_code",
            "join_status",
            "device_class",
            "regulation_number",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in result["rows"]:
            record = {key: row.get(key, "") for key in fields}
            record.update(
                device_class=(row["classification"] or {}).get("device_class", ""),
                regulation_number=(row["classification"] or {}).get(
                    "regulation_number", ""
                ),
            )
            # Neutralize spreadsheet formulas in externally supplied strings.
            writer.writerow(
                {
                    k: "'" + v
                    if isinstance(v, str) and v.startswith(("=", "+", "-", "@"))
                    else v
                    for k, v in record.items()
                }
            )
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
