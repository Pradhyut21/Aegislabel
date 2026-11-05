from io import BytesIO
import zipfile
import json
import copy
import fitz
from backend.main import Session, Record
from backend.domain import artwork_hash, pdf
import hashlib


def test_warning_failure_correction_review_release(client):
    c = client
    result = c.post(
        "/api/v1/changes",
        json={
            "device_id": "device-cardiac",
            "warning": "Do not reuse. Inspect packaging before use.",
        },
    )
    assert result.status_code == 200
    change = result.json()
    assert set(change["affected_labels"]) == {
        "label-cardiac-unit",
        "label-cardiac-carton",
    }
    draft = c.post("/api/v1/drafts", json={"label_id": "label-cardiac-unit"}).json()
    assert "Inspect packaging" in draft["fields"]["warning"]
    fields = {**draft["fields"], "warning": "Do not reuse."}
    bad = c.put(
        "/api/v1/drafts/" + draft["id"],
        json={"revision": draft["revision"], "fields": fields},
    ).json()
    v = c.post("/api/v1/drafts/" + bad["id"] + "/validate").json()
    assert v["decision"] == "BLOCKED"
    assert any(
        f["reason_code"] == "SAFETY_WARNING_MISMATCH" and not f["passed"]
        for f in v["findings"]
    )
    assert c.post("/api/v1/drafts/" + bad["id"] + "/release").status_code == 409
    # Unauthorized users cannot review even valid drafts.
    good = c.post("/api/v1/drafts", json={"label_id": "label-cardiac-unit"}).json()
    assert (
        c.post("/api/v1/drafts/" + good["id"] + "/validate").json()["decision"]
        == "PASS FOR REVIEW"
    )
    state = c.get("/api/v1/workspace").json()
    good = next(d for d in state["draft"] if d["id"] == good["id"])
    good = c.post(
        "/api/v1/drafts/" + good["id"] + "/review",
        json={"revision": good["revision"], "action": "submit"},
    ).json()
    assert (
        c.post(
            "/api/v1/drafts/" + good["id"] + "/review",
            json={"revision": good["revision"], "action": "approve"},
        ).status_code
        == 403
    )
    r = c.post(
        "/api/v1/auth/login",
        json={"username": "reviewer", "password": "Aegis-reviewer-2026!"},
    )
    c.headers["x-csrf-token"] = r.json()["csrf"]
    approved = c.post(
        "/api/v1/drafts/" + good["id"] + "/review",
        json={"revision": good["revision"], "action": "approve"},
    )
    assert approved.status_code == 200, approved.text
    approved = approved.json()
    assert approved["approval"]["hash"] == artwork_hash(approved["fields"])
    released = c.post("/api/v1/drafts/" + good["id"] + "/release")
    assert released.status_code == 200, released.text
    download = c.get("/api/v1/releases/" + released.json()["id"] + "/download")
    assert download.status_code == 200
    with zipfile.ZipFile(BytesIO(download.content)) as z:
        assert set(z.namelist()) == {
            "label.svg",
            "label.pdf",
            "release-summary.json",
            "source-evidence.json",
        }
        summary = json.loads(z.read("release-summary.json"))
        assert (
            summary["artwork_hash"] == hashlib.sha256(z.read("label.svg")).hexdigest()
        )
        pdfdoc = fitz.open(stream=z.read("label.pdf"), filetype="pdf")
        assert "Inspect packaging before use." in pdfdoc[0].get_text()
    # Artwork changes preserve previous release but new revision inherits no approval.
    edited = c.put(
        "/api/v1/drafts/" + approved["id"],
        json={
            "revision": approved["revision"] + 2,
            "fields": {**approved["fields"], "claims": "Unapproved claim"},
        },
    )
    # Optimistic version numbers may have advanced on release; fetch latest before editing.
    current = next(
        d
        for d in c.get("/api/v1/workspace").json()["draft"]
        if d["id"] == approved["id"]
    )
    if edited.status_code != 200:
        edited = c.put(
            "/api/v1/drafts/" + current["id"],
            json={
                "revision": current["revision"],
                "fields": {**current["fields"], "claims": "Unapproved claim"},
            },
        )
    assert edited.status_code == 200
    assert edited.json()["approval"] is None
    assert (
        c.post("/api/v1/drafts/" + edited.json()["id"] + "/release").status_code == 409
    )
    assert c.get("/api/v1/audit/verify").json()["valid"]


def test_source_change_invalidates_approval(client):
    c = client
    c.post(
        "/api/v1/changes",
        json={"device_id": "device-infusion", "warning": "Do not reuse. New warning."},
    )
    # Seed approval still exists as historical evidence but cannot release against a newer source.
    r = c.post("/api/v1/drafts/artwork-infusion-unit-1/release")
    assert r.status_code == 409


def test_revision_conflict_and_unknown_records(client):
    assert (
        client.put(
            "/api/v1/drafts/artwork-monitor-unit-1",
            json={"revision": 999, "fields": {}},
        ).status_code
        == 422
    )
    fields = client.get("/api/v1/workspace").json()["draft"][0]["fields"]
    assert (
        client.put(
            "/api/v1/drafts/artwork-monitor-unit-1",
            json={"revision": 999, "fields": fields},
        ).status_code
        == 409
    )
    assert client.post("/api/v1/drafts/missing/validate").status_code == 404


def test_mutation_execution_isolation_and_controls(client):
    before = client.get("/api/v1/workspace").json()
    r = client.post("/api/v1/benchmarks")
    assert r.status_code == 200
    b = r.json()
    assert b["total"] >= 20
    assert b["detected"] == b["total"]
    assert b["false_blocks"] == 0
    after = client.get("/api/v1/workspace").json()
    for key in ["draft", "document", "label"]:
        assert before[key] == after[key]
    assert all(row["execution_ms"] >= 0 and row["rules"] for row in b["rows"])


def test_security(client):
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as anonymous:
        assert anonymous.get("/api/v1/workspace").status_code == 401
        assert (
            anonymous.post(
                "/api/v1/auth/login", json={"username": "author", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post("/api/v1/benchmarks", headers={"x-csrf-token": "wrong"}).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/benchmarks", headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert client.get("/api/v1/health").headers["x-content-type-options"] == "nosniff"


def test_pdf_extraction_and_source_confirmation(client):
    fields = client.get("/api/v1/workspace").json()["draft"][0]["fields"]
    r = client.post(
        "/api/v1/documents/upload?device_id=device-cardiac",
        files={"file": ("../../hostile.pdf", pdf(fields), "application/pdf")},
    )
    assert r.status_code == 200, r.text
    candidate = r.json()
    assert candidate["title"] == "hostile.pdf"
    assert candidate["status"] == "candidate"
    assert candidate["fields"]["warning"] == fields["warning"]
    assert candidate["evidence"]["warning"]["page"] == 1
    assert (
        client.post("/api/v1/documents/" + candidate["id"] + "/approve").status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/documents/upload?device_id=device-cardiac",
            files={"file": ("bad.pdf", b"not a PDF", "application/pdf")},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/documents/upload?device_id=device-cardiac",
            files={"file": ("bad.pdf", b"%PDF-broken", "application/pdf")},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/documents/upload?device_id=device-cardiac",
            files={
                "file": (
                    "big.pdf",
                    b"%PDF-" + b"X" * (10 * 1024 * 1024),
                    "application/pdf",
                )
            },
        ).status_code
        == 413
    )


def test_audit_tampering_detected(client):
    with Session.begin() as s:
        row = next(
            x
            for x in s.query(Record).filter_by(kind="audit")
            if x.data["sequence"] == 1
        )
        row_id = row.id
        original = copy.deepcopy(row.data)
        row.data = {**row.data, "actor": "tampered"}
    assert not client.get("/api/v1/audit/verify").json()["valid"]
    with Session.begin() as s:
        s.get(Record, row_id).data = original
    assert client.get("/api/v1/audit/verify").json()["valid"]


def test_targeted_mutations_follow_changed_fields(client):
    change = client.post(
        "/api/v1/changes",
        json={
            "device_id": "device-cardiac",
            "warning": "Do not reuse. Inspect packaging before use.",
        },
    ).json()
    result = client.post("/api/v1/benchmarks", json={"change_id": change["id"]}).json()
    assert result["selection"] == "change-targeted"
    assert result["total"] < 24
    assert any("warning" in r["mutation"] for r in result["rows"])
    assert not any(r["scenario"] == "Wrong device identifier" for r in result["rows"])


def test_login_rate_limit_is_enforced(client):
    from backend.main import rates

    for _ in range(21):
        response = client.post(
            "/api/v1/auth/login", json={"username": "unknown", "password": "bad"}
        )
    assert response.status_code == 429
    rates.clear()


def test_reviewer_confirms_pdf_and_conflicting_source_stays_unapproved(client):
    from tests.test_documents import make_pdf

    fields = client.get("/api/v1/workspace").json()["draft"][0]["fields"]
    candidate = client.post(
        "/api/v1/documents/upload?device_id=device-monitor",
        files={"file": ("source.pdf", pdf(fields), "application/pdf")},
    ).json()
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "reviewer", "password": "Aegis-reviewer-2026!"},
    )
    client.headers["x-csrf-token"] = r.json()["csrf"]
    result = client.post("/api/v1/documents/" + candidate["id"] + "/approve")
    assert result.status_code == 200, result.text
    assert (
        client.post("/api/v1/documents/" + candidate["id"] + "/approve").status_code
        == 409
    )
    conflict = client.post(
        "/api/v1/documents/upload?device_id=device-monitor",
        files={
            "file": (
                "source.pdf",
                make_pdf("warning: Do not reuse.\nwarning: Reuse permitted."),
                "application/pdf",
            )
        },
    ).json()
    assert conflict["contradiction"]
    assert (
        client.post("/api/v1/documents/" + conflict["id"] + "/approve").status_code
        == 409
    )


def test_unrelated_source_field_does_not_advance_label_dependencies(client):
    c = client
    fields = c.get("/api/v1/workspace").json()["draft"][0]["fields"]
    fields = {**fields, "packaging": "Shipping carton"}
    candidate = c.post(
        "/api/v1/documents/upload?device_id=device-cardiac",
        files={"file": ("packaging-only.pdf", pdf(fields), "application/pdf")},
    ).json()
    r = c.post(
        "/api/v1/auth/login",
        json={"username": "reviewer", "password": "Aegis-reviewer-2026!"},
    )
    c.headers["x-csrf-token"] = r.json()["csrf"]
    before = {
        label["id"]: label["source_id"]
        for label in c.get("/api/v1/workspace").json()["label"]
    }
    change = c.post("/api/v1/documents/" + candidate["id"] + "/approve").json()
    assert change["affected_labels"] == []
    after = {
        label["id"]: label["source_id"]
        for label in c.get("/api/v1/workspace").json()["label"]
    }
    assert before == after


def test_newer_artwork_prevents_release_of_earlier_approval(client):
    original = "artwork-cardiac-unit-1"
    source = next(
        d
        for d in client.get("/api/v1/workspace").json()["draft"]
        if d["id"] == original
    )
    new = client.put(
        "/api/v1/drafts/" + original,
        json={"revision": source["revision"], "fields": source["fields"]},
    ).json()
    assert new["approval"] is None
    assert client.post("/api/v1/drafts/" + original + "/release").status_code == 409
    assert not next(
        d
        for d in client.get("/api/v1/workspace").json()["draft"]
        if d["id"] == original
    )["approval_current"]
