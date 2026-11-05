"""Read-only research metadata joins. Never populates authoritative label sources."""

from collections import defaultdict


def combine_references(udi_records, classification_records):
    """Join only by explicit FDA product code; preserve missing/ambiguous matches.

    An allowlist excludes contacts, GMDN content, narratives and unapproved warnings.
    Product-code joins express a regulatory category, never device equivalence.
    """
    classifications = defaultdict(list)
    for record in classification_records:
        code = record.get("product_code")
        if code:
            classifications[code].append(record)
    rows = []
    seen = set()
    skipped = 0
    for record in udi_records:
        key = record.get("public_device_record_key")
        if not key:
            skipped += 1
            continue
        for product in record.get("product_codes", []):
            code = product.get("code")
            if not code:
                continue
            identity = (key, str(record.get("public_version_number", "")), code)
            if identity in seen:
                continue
            seen.add(identity)
            matches = classifications.get(code, [])
            classification = None
            conflicts = []
            if len(matches) == 1:
                match = matches[0]
                classification = {
                    field: match.get(field)
                    for field in [
                        "product_code",
                        "device_name",
                        "device_class",
                        "regulation_number",
                        "medical_specialty_description",
                    ]
                }
                embedded = product.get("openfda", {})
                for field in ["device_class", "regulation_number"]:
                    if (
                        embedded.get(field)
                        and match.get(field)
                        and str(embedded[field]) != str(match[field])
                    ):
                        conflicts.append(
                            dict(
                                field=field,
                                udi_reference=embedded[field],
                                classification_reference=match[field],
                            )
                        )
            rows.append(
                dict(
                    udi_record_id=key,
                    udi_public_version=str(record.get("public_version_number", "")),
                    udi_public_version_date=record.get("public_version_date"),
                    brand_name=record.get("brand_name"),
                    model_number=record.get("version_or_model_number"),
                    primary_identifiers=[
                        {
                            "id": identifier.get("id"),
                            "issuing_agency": identifier.get("issuing_agency"),
                        }
                        for identifier in record.get("identifiers", [])
                        if identifier.get("type") == "Primary"
                    ],
                    single_use=record.get("is_single_use"),
                    sterile=record.get("sterilization", {}).get("is_sterile"),
                    product_code=code,
                    classification=classification,
                    source_references={
                        "udi": record.get("_source"),
                        "classification": matches[0].get("_source")
                        if len(matches) == 1
                        else None,
                    },
                    join_status="matched_category"
                    if len(matches) == 1
                    else "missing_classification"
                    if not matches
                    else "ambiguous_classification",
                    reference_conflicts=conflicts,
                    permitted_use="Research reference only; not approved labeling evidence or clinical advice",
                )
            )
    return dict(
        rows=rows,
        summary=dict(
            joined_rows=len(rows),
            unique_devices=len({row["udi_record_id"] for row in rows}),
            matched=sum(row["join_status"] == "matched_category" for row in rows),
            unmatched=sum(
                row["join_status"] == "missing_classification" for row in rows
            ),
            ambiguous=sum(
                row["join_status"] == "ambiguous_classification" for row in rows
            ),
            conflicting=sum(bool(row["reference_conflicts"]) for row in rows),
            skipped_without_identity=skipped,
        ),
    )
