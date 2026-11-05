import pytest
from backend.domain import (
    FIELDS,
    RULESET,
    validate,
    artwork_hash,
    svg,
    pdf,
    impact_experiment,
)


@pytest.fixture
def fields():
    return {k: "approved-" + k for k in FIELDS}


@pytest.mark.parametrize("field", list(FIELDS))
def test_each_control_blocks_corruption(fields, field):
    mutant = {**fields, field: "CORRUPTED"}
    r = validate(mutant, fields, 2, 2)
    assert r["decision"] == "BLOCKED"
    assert any(f["field"] == field and not f["passed"] for f in r["findings"])


def test_pass_and_stale_source(fields):
    assert validate(fields, fields, 2, 2)["decision"] == "PASS FOR REVIEW"
    assert validate(fields, fields, 1, 2)["decision"] == "BLOCKED"


def test_hash_changes_for_every_controlled_field(fields):
    for k in fields:
        assert artwork_hash({**fields, k: "changed"}) != artwork_hash(fields), k


def test_approval_hash_source_ruleset_binding(fields):
    a = dict(hash=artwork_hash(fields), source_version=2, ruleset=RULESET)
    assert validate(fields, fields, 2, 2, a, True)["decision"] == "PASS FOR REVIEW"
    for key in ["hash", "source_version", "ruleset"]:
        assert (
            validate(fields, fields, 2, 2, {**a, key: "wrong"}, True)["decision"]
            == "BLOCKED"
        )


def test_xml_is_escaped(fields):
    f = {**fields, "name": "<script>alert(1)</script>"}
    assert "<script>" not in svg(f)


def test_pdf_and_svg_generated(fields):
    assert pdf(fields).startswith(b"%PDF-")
    assert "<svg" in svg(fields)


def test_source_conflict_escalates(fields):
    assert validate(fields, fields, 2, 2, contradiction=True)["decision"] == "ESCALATE"


def test_explicit_dependency_impact_and_unrelated_labels():
    r = impact_experiment()
    assert r["recall"] == 1
    assert r["false_positive"] == 0
    assert all(c["observed"] == c["expected"] for c in r["cases"])


def test_mutation_harness_exposes_disabled_control(fields, monkeypatch):
    import backend.domain as domain

    original = domain.validate

    def disabled(*args, **kwargs):
        r = original(*args, **kwargs)
        # Simulate losing the warning comparison while leaving other controls intact.
        r["findings"] = [f for f in r["findings"] if f["field"] != "warning"]
        r["decision"] = (
            "BLOCKED"
            if any(not f["passed"] for f in r["findings"])
            else "PASS FOR REVIEW"
        )
        return r

    monkeypatch.setattr(domain, "validate", disabled)
    b = domain.benchmark(fields, 2)
    assert any(
        not r["actual_detection"] and "warning" in r["mutation"] for r in b["rows"]
    )


def test_real_pdf_barcode_decodes():
    import fitz
    import zxingcpp

    fields = {k: "controlled-" + k for k in FIELDS}
    fields["barcode"] = "09506000134352"
    document = fitz.open(stream=pdf(fields), filetype="pdf")
    pix = document[0].get_pixmap(matrix=fitz.Matrix(2, 2))
    from PIL import Image

    pixels = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    decoded = zxingcpp.read_barcodes(pixels)
    assert any(result.text == fields["barcode"] for result in decoded)


def test_generated_source_evidence_resolves():
    from backend.documents import generated_evidence

    fields = {k: "controlled-" + k for k in FIELDS}
    fields["barcode"] = "09506000134352"
    evidence = generated_evidence(fields)
    assert all(evidence[k]["page"] and evidence[k]["bbox"] for k in fields)
