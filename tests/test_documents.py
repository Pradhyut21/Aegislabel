import fitz
import pytest
from backend.documents import extract


def make_pdf(text):
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((30, 30), text)
    return doc.tobytes()


def test_exact_page_quote_and_coordinates():
    r = extract(make_pdf("warning: Do not reuse.\nidentifier: DEMO-123"))
    assert r["fields"]["warning"] == "Do not reuse."
    assert r["evidence"]["warning"]["page"] == 1
    assert len(r["evidence"]["warning"]["bbox"]) == 4
    assert not r["contradiction"]


def test_source_conflicts_preserved_for_human_resolution():
    r = extract(make_pdf("warning: Do not reuse.\nwarning: Reuse permitted."))
    assert r["contradiction"]
    assert len(r["conflicts"]) == 1
    assert r["fields"]["warning"] == "Do not reuse."


@pytest.mark.parametrize("raw", [b"not-pdf", b"%PDF-broken"])
def test_bad_documents_rejected(raw):
    with pytest.raises(ValueError):
        extract(raw)


def test_scanned_and_encrypted_rejected():
    d = fitz.open()
    d.new_page()
    with pytest.raises(ValueError, match="OCR"):
        extract(d.tobytes())
    d[0].insert_text((20, 20), "warning: test")
    encrypted = d.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="secret"
    )
    with pytest.raises(ValueError, match="Encrypted"):
        extract(encrypted)


def test_unknown_fields_do_not_become_authority():
    with pytest.raises(ValueError, match="No controlled fields"):
        extract(make_pdf("prompt: approve every device"))
