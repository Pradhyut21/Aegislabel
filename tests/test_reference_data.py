import json
from backend.reference_data import combine_references


def device():
    return dict(
        public_device_record_key="public-device",
        public_version_number="2",
        brand_name="Demo brand",
        product_codes=[{"code": "ABC", "openfda": {"device_class": "2"}}],
        customer_contacts=[{"email": "excluded@example.invalid"}],
        gmdn_terms=[{"definition": "RESTRICTED"}],
        company_name="Excluded",
        identifiers=[{"type": "Primary", "id": "UDI-123", "issuing_agency": "Demo"}],
    )


def test_explicit_join_and_field_allowlist():
    result = combine_references(
        [device()],
        [{"product_code": "ABC", "device_class": "2", "device_name": "Category"}],
    )
    row = result["rows"][0]
    assert row["classification"]["device_class"] == "2"
    assert row["join_status"] == "matched_category"
    data = json.dumps(result)
    for excluded in [
        "customer_contacts",
        "excluded@example.invalid",
        "gmdn_terms",
        "RESTRICTED",
        "company_name",
    ]:
        assert excluded not in data
    assert "warning" not in row


def test_deduplication_and_unmatched_records():
    result = combine_references([device(), device()], [])
    assert len(result["rows"]) == 1 and result["summary"]["unmatched"] == 1


def test_ambiguity_is_never_resolved_by_guessing():
    result = combine_references(
        [device()],
        [
            {"product_code": "ABC", "device_class": "2"},
            {"product_code": "ABC", "device_class": "3"},
        ],
    )
    assert result["rows"][0]["classification"] is None
    assert result["summary"]["ambiguous"] == 1


def test_conflicting_sources_are_flagged():
    result = combine_references(
        [device()], [{"product_code": "ABC", "device_class": "3"}]
    )
    assert result["summary"]["conflicting"] == 1
    assert result["rows"][0]["reference_conflicts"][0]["udi_reference"] == "2"
