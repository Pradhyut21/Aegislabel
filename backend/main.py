import os
import secrets
import hashlib
import hmac
import time
import uuid
import json
import zipfile
import threading
import logging
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from collections import defaultdict, deque
import fitz
from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile, File
from fastapi.responses import Response as RawResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .security import RequestGuard
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from .db import Base, engine, Session, Record
from .domain import (
    FIELDS,
    RULESET,
    SOURCE_FIELDS,
    artwork_hash,
    assess_impact,
    benchmark,
    digest,
    pdf,
    svg,
    validate,
    field_errors,
)
from .provider import propose, enabled
from .documents import extract, generated_evidence

app = FastAPI(title="AegisLabel-FX", version="1.0.0")
lock = threading.RLock()
rates = defaultdict(deque)


def now():
    return datetime.now(timezone.utc).isoformat()


def ident():
    return uuid.uuid4().hex


def add(s, kind, data, id=None):
    r = Record(id=id or ident(), kind=kind, data=data, revision=1)
    s.add(r)
    return r


def get(s, id, kind=None):
    r = s.get(Record, id)
    if not r or kind and r.kind != kind:
        raise HTTPException(404, "Record not found")
    return r


def items(s, kind):
    return list(s.scalars(select(Record).where(Record.kind == kind)))


def out(r):
    return dict(id=r.id, revision=r.revision, **r.data)


def update(r, **changes):
    r.data = {**r.data, **changes}
    r.revision += 1


def audit(s, action, actor, detail):
    records = sorted(items(s, "audit"), key=lambda r: r.data["sequence"])
    previous = records[-1].data["hash"] if records else "0" * 64
    payload = dict(
        sequence=len(records) + 1,
        timestamp=now(),
        action=action,
        actor=actor,
        detail=detail,
        previous_hash=previous,
    )
    add(s, "audit", {**payload, "hash": digest(payload)})


def verify_chain(s):
    previous = "0" * 64
    for n, r in enumerate(
        sorted(items(s, "audit"), key=lambda r: r.data["sequence"]), 1
    ):
        d = dict(r.data)
        h = d.pop("hash")
        if d["previous_hash"] != previous or d["sequence"] != n or digest(d) != h:
            return dict(valid=False, checked=n, failed_sequence=n)
        previous = h
    return dict(valid=True, checked=len(items(s, "audit")), head=previous)


def hash_password(password, salt):
    return hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1
    ).hex()


def seed():
    Base.metadata.create_all(engine)
    with Session.begin() as s:
        if s.get(Record, "device-cardiac"):
            return
        for name, role in [("author", "author"), ("reviewer", "reviewer")]:
            salt = secrets.token_hex(16)
            password = os.getenv(
                "DEMO_" + name.upper() + "_PASSWORD", f"Aegis-{name}-2026!"
            )
            add(
                s,
                "user",
                dict(
                    username=name,
                    role=role,
                    salt=salt,
                    password_hash=hash_password(password, salt),
                ),
                name,
            )
        devices = [
            ("cardiac", "Sterile Cardiac Procedure Kit", "CK-240", "Sterile"),
            ("infusion", "Infusion Administration Set", "IA-120", "Sterile"),
            ("monitor", "Patient Monitoring Accessory", "PM-080", "Non-sterile"),
        ]
        for index, (slug, name, code, sterile) in enumerate(devices):
            did = "device-" + slug
            add(
                s,
                "device",
                dict(
                    name=name,
                    identifier=code,
                    synthetic=True,
                    description="Fictional demonstration device. Not for clinical use.",
                    markets=["EU", "US"],
                    languages=["en", "de"],
                    variants=["Standard", "Compact"],
                ),
                did,
            )
            fields = dict(
                name=name,
                identifier=code,
                variant="Standard",
                udi=f"095060001343{index}5",
                barcode=f"095060001343{index}5",
                warning="Do not reuse.",
                ifu=f"IFU-{code} / R1",
                packaging="Unit pouch",
                symbols="Single use; Consult IFU",
                claims="Approved intended use only",
                language="en",
                translation="Do not reuse.",
                manufacturer="Aegis Synthetic Devices Ltd.",
                sterilization=sterile,
                market="EU",
            )
            doc = add(
                s,
                "document",
                dict(
                    device_id=did,
                    title=f"{code} Approved Specification",
                    source_revision=1,
                    status="approved",
                    fields=fields,
                    evidence=generated_evidence(fields),
                    mode="deterministic",
                    created_at=now(),
                ),
                "spec-" + slug + "-1",
            )
            for suffix, packaging, variant, market in [
                ("unit", "Unit pouch", "Standard", "EU"),
                ("carton", "Carton", "Compact", "US"),
            ]:
                f = {
                    **fields,
                    "packaging": packaging,
                    "variant": variant,
                    "market": market,
                }
                lid = "label-" + slug + "-" + suffix
                add(
                    s,
                    "label",
                    dict(
                        device_id=did,
                        name=f"{code} · {variant} · {packaging}",
                        market=market,
                        language="en",
                        packaging=packaging,
                        variant=variant,
                        source_id=doc.id,
                        dependency_fields=SOURCE_FIELDS,
                    ),
                    lid,
                )
                a = dict(
                    hash=artwork_hash(f),
                    source_version=1,
                    ruleset=RULESET,
                    reviewer="reviewer",
                    timestamp=now(),
                    seed=True,
                )
                add(
                    s,
                    "draft",
                    dict(
                        label_id=lid,
                        device_id=did,
                        fields=f,
                        source_id=doc.id,
                        source_version=1,
                        label_revision=1,
                        status="approved",
                        author="seed",
                        approval=a,
                        mode="deterministic",
                        created_at=now(),
                        validation=None,
                    ),
                    "artwork-" + slug + "-" + suffix + "-1",
                )
        audit(s, "WORKSPACE_INITIALIZED", "system", {"synthetic": True})


seed()


@app.middleware("http")
async def security(request: Request, call_next):
    if request.url.path.startswith("/api"):
        ip = request.client.host if request.client else "local"
        key = (ip, "login" if request.url.path.endswith("/login") else "api")
        q = rates[key]
        t = time.monotonic()
        while q and q[0] < t - 60:
            q.popleft()
        if len(q) >= (20 if key[1] == "login" else 400):
            return RawResponse("Rate limit exceeded", 429)
        q.append(t)
        try:
            content_length = int(request.headers.get("content-length", "0") or 0)
        except ValueError:
            return RawResponse("Invalid content length", 400)
        if content_length > 11 * 1024 * 1024:
            return RawResponse("Request exceeds 10 MB", 413)
        if request.method not in ["GET", "HEAD", "OPTIONS"]:
            origin = request.headers.get("origin")
            allowed = {
                str(request.base_url).rstrip("/"),
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            }
            if origin and origin not in allowed:
                return RawResponse("Origin rejected", 403)
    try:
        response = await call_next(request)
    except Exception:
        logging.exception("API operation failed")
        return RawResponse("Internal server error. Consult local server logs.", 500)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'"
    )
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


def user(request: Request):
    token = request.cookies.get("aegis_session", "")
    with Session() as s:
        r = s.get(Record, "session-" + hashlib.sha256(token.encode()).hexdigest())
        if not r or r.data["expires"] < time.time():
            raise HTTPException(401, "Sign in to continue")
        if request.method not in ["GET", "HEAD"] and not hmac.compare_digest(
            request.headers.get("x-csrf-token", ""), r.data["csrf"]
        ):
            raise HTTPException(403, "Invalid CSRF token")
        return dict(
            username=r.data["username"], role=r.data["role"], csrf=r.data["csrf"]
        )


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Strict):
    username: str = Field(max_length=80)
    password: str = Field(max_length=200)


@app.post("/api/v1/auth/login")
def login(body: Login, response: Response):
    with lock, Session.begin() as s:
        u = s.get(Record, body.username)
        valid_user = bool(u and u.kind == "user")
        salt = u.data["salt"] if valid_user else "00" * 16
        observed = hash_password(body.password, salt)
        expected = u.data["password_hash"] if valid_user else "00" * 64
        if not hmac.compare_digest(observed, expected) or not valid_user:
            raise HTTPException(401, "Invalid credentials")
        sessions = items(s, "session")
        for session in sessions:
            if session.data["expires"] < time.time():
                s.delete(session)
        own = sorted(
            [
                session
                for session in sessions
                if session.data["username"] == body.username
                and session.data["expires"] >= time.time()
            ],
            key=lambda session: session.data["expires"],
        )
        for session in own[:-19]:
            s.delete(session)
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        add(
            s,
            "session",
            dict(
                username=body.username,
                role=u.data["role"],
                csrf=csrf,
                expires=time.time() + 28800,
            ),
            "session-" + hashlib.sha256(token.encode()).hexdigest(),
        )
        response.set_cookie(
            "aegis_session",
            token,
            httponly=True,
            samesite="strict",
            max_age=28800,
            secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        )
        audit(s, "SIGN_IN", body.username, {})
        return dict(username=body.username, role=u.data["role"], csrf=csrf)


@app.get("/api/v1/auth/me")
def me(u=Depends(user)):
    return u


@app.post("/api/v1/auth/logout")
def logout(request: Request, response: Response, u=Depends(user)):
    with lock, Session.begin() as s:
        r = s.get(
            Record,
            "session-"
            + hashlib.sha256(
                request.cookies.get("aegis_session", "").encode()
            ).hexdigest(),
        )
        if r:
            s.delete(r)
        audit(s, "SIGN_OUT", u["username"], {})
    response.delete_cookie("aegis_session")
    return {"ok": True}


@app.get("/api/v1/health")
def health():
    return dict(
        status="ok",
        mode="ai-assisted" if enabled() else "deterministic",
        ruleset=RULESET,
    )


@app.get("/api/v1/workspace")
def workspace(u=Depends(user)):
    with Session() as s:
        result = {
            kind: [out(x) for x in items(s, kind)]
            for kind in [
                "device",
                "document",
                "label",
                "draft",
                "change",
                "validation",
                "benchmark",
                "audit",
                "release",
            ]
        }
        for kind in [
            "document",
            "draft",
            "change",
            "validation",
            "benchmark",
            "release",
        ]:
            result[kind].sort(key=lambda record: record.get("created_at", ""))
        result["audit"].sort(key=lambda event: event["sequence"])
        for d in result["draft"]:
            source = current_source(s, get(s, d["label_id"], "label"))
            a = d.get("approval")
            latest_revision = max(
                x["label_revision"]
                for x in result["draft"]
                if x["label_id"] == d["label_id"]
            )
            d["approval_current"] = bool(
                d["label_revision"] == latest_revision
                and a
                and a["hash"] == artwork_hash(d["fields"])
                and a["source_version"] == source.data["source_revision"]
                and a["ruleset"] == RULESET
            )
        return result


def current_source(s, label):
    return get(s, label.data["source_id"], "document")


def expected_fields(doc, label):
    return {
        **doc.data["fields"],
        **{k: label.data[k] for k in ["variant", "market", "language", "packaging"]},
    }


def do_source(s, device_id, fields, title, actor, evidence=None, mode="deterministic"):
    docs = [
        d
        for d in items(s, "document")
        if d.data["device_id"] == device_id and d.data["status"] == "approved"
    ]
    old = max(docs, key=lambda d: d.data["source_revision"])
    version = old.data["source_revision"] + 1
    doc = add(
        s,
        "document",
        dict(
            device_id=device_id,
            title=title,
            source_revision=version,
            status="approved",
            fields=fields,
            evidence=evidence or generated_evidence(fields),
            mode=mode,
            created_at=now(),
        ),
    )
    changed = [
        dict(field=k, old=old.data["fields"].get(k), new=fields.get(k))
        for k in FIELDS
        if old.data["fields"].get(k) != fields.get(k)
    ]
    affected = assess_impact(
        device_id,
        [c["field"] for c in changed],
        [out(label) for label in items(s, "label")],
    )
    for label_id in affected:
        update(get(s, label_id, "label"), source_id=doc.id)
    for previous_change in items(s, "change"):
        if (
            bool(affected)
            and previous_change.data["device_id"] == device_id
            and previous_change.data["status"] == "pending"
        ):
            update(previous_change, status="superseded")
    change = add(
        s,
        "change",
        dict(
            device_id=device_id,
            old_source_id=old.id,
            new_source_id=doc.id,
            old_version=version - 1,
            new_version=version,
            changes=changed,
            affected_labels=affected,
            status="pending" if affected else "no-impact",
            created_at=now(),
        ),
    )
    audit(
        s,
        "SOURCE_APPROVED",
        actor,
        dict(source_id=doc.id, change_id=change.id, affected_labels=affected),
    )
    return out(change)


class ChangeInput(Strict):
    device_id: str
    warning: str = Field(min_length=1, max_length=240)


@app.post("/api/v1/changes")
def change(body: ChangeInput, u=Depends(user)):
    if not body.warning.strip():
        raise HTTPException(422, "Warning cannot be blank")
    with lock, Session.begin() as s:
        get(s, body.device_id, "device")
        docs = [
            d
            for d in items(s, "document")
            if d.data["device_id"] == body.device_id and d.data["status"] == "approved"
        ]
        old = max(docs, key=lambda d: d.data["source_revision"])
        f = {**old.data["fields"], "warning": body.warning, "translation": body.warning}
        return do_source(s, body.device_id, f, old.data["title"], u["username"])


class DraftInput(Strict):
    label_id: str


@app.post("/api/v1/drafts")
def create_draft(body: DraftInput, u=Depends(user)):
    with lock, Session.begin() as s:
        label = get(s, body.label_id, "label")
        doc = current_source(s, label)
        prev = [d for d in items(s, "draft") if d.data["label_id"] == label.id]
        revision = max(d.data["label_revision"] for d in prev) + 1
        proposal = propose(expected_fields(doc, label))
        r = add(
            s,
            "draft",
            dict(
                label_id=label.id,
                device_id=label.data["device_id"],
                fields=proposal["fields"],
                source_id=doc.id,
                source_version=doc.data["source_revision"],
                label_revision=revision,
                status="draft",
                author=u["username"],
                approval=None,
                mode=proposal["mode"],
                provider_error=proposal["provider_error"],
                usage=proposal["usage"],
                created_at=now(),
                validation=None,
            ),
        )
        audit(
            s,
            "DRAFT_CREATED",
            u["username"],
            dict(draft_id=r.id, hash=artwork_hash(r.data["fields"])),
        )
        return out(r)


class EditInput(Strict):
    revision: int
    fields: dict[str, str]


@app.put("/api/v1/drafts/{id}")
def edit(id: str, body: EditInput, u=Depends(user)):
    if set(body.fields) != set(FIELDS) or any(
        len(v) > 240 for v in body.fields.values()
    ):
        raise HTTPException(
            422, "Provide all controlled fields; maximum 240 characters per field"
        )
    if field_errors(body.fields):
        raise HTTPException(422, "; ".join(field_errors(body.fields)))
    with lock, Session.begin() as s:
        r = get(s, id, "draft")
        if r.revision != body.revision:
            raise HTTPException(409, "Artwork changed. Refresh before saving.")
        # Editing creates an immutable successor; existing reviewed artwork is preserved.
        prev = [
            d for d in items(s, "draft") if d.data["label_id"] == r.data["label_id"]
        ]
        n = add(
            s,
            "draft",
            {
                **r.data,
                "fields": body.fields,
                "label_revision": max(d.data["label_revision"] for d in prev) + 1,
                "status": "draft",
                "approval": None,
                "validation": None,
                "author": u["username"],
                "created_at": now(),
                "parent_id": r.id,
            },
        )
        audit(
            s,
            "ARTWORK_REVISED_APPROVAL_INVALIDATED",
            u["username"],
            dict(parent_id=id, draft_id=n.id, hash=artwork_hash(body.fields)),
        )
        return out(n)


def run_validation(s, r, actor, release=False):
    label = get(s, r.data["label_id"], "label")
    doc = current_source(s, label)
    result = validate(
        r.data["fields"],
        expected_fields(doc, label),
        r.data["source_version"],
        doc.data["source_revision"],
        r.data.get("approval"),
        release,
        doc.data.get("contradiction", False),
    )
    for finding in result["findings"]:
        finding["source_id"] = doc.id
        finding["source_reference"] = (
            f"{doc.data['title']} / R{doc.data['source_revision']} / {finding['field']}"
        )
        finding["source_record_id"] = doc.id
        finding["source_kind"] = "document"
        if finding["field"] in ["variant", "market", "language", "packaging"]:
            finding["source_reference"] = (
                f"Label registry {label.id} / revision {label.revision} / {finding['field']}"
            )
            finding["source_record_id"] = label.id
            finding["source_kind"] = "registry"
        elif finding["field"] == "approval":
            finding["source_reference"] = f"Artwork approval / {r.id}"
            finding["source_record_id"] = r.id
            finding["source_kind"] = "approval"

    v = add(
        s,
        "validation",
        dict(draft_id=r.id, source_id=doc.id, created_at=now(), **result),
    )
    update(r, validation=v.id)
    audit(
        s,
        "VALIDATION_EXECUTED",
        actor,
        dict(draft_id=r.id, validation_id=v.id, decision=result["decision"]),
    )
    return out(v)


@app.post("/api/v1/drafts/{id}/validate")
def check(id: str, u=Depends(user)):
    with lock, Session.begin() as s:
        return run_validation(s, get(s, id, "draft"), u["username"])


class ReviewInput(Strict):
    revision: int
    action: str = Field(pattern="^(submit|approve|reject)$")
    comment: str = Field(default="", max_length=1000)


@app.post("/api/v1/drafts/{id}/review")
def review(id: str, body: ReviewInput, u=Depends(user)):
    with lock, Session.begin() as s:
        r = get(s, id, "draft")
        if r.revision != body.revision:
            raise HTTPException(409, "Artwork changed. Refresh review.")
        revisions = [
            d for d in items(s, "draft") if d.data["label_id"] == r.data["label_id"]
        ]
        if r.data["label_revision"] != max(d.data["label_revision"] for d in revisions):
            raise HTTPException(
                409, "A newer artwork revision exists. Review the latest revision."
            )
        if body.action == "submit":
            result = run_validation(s, r, u["username"])
            if result["decision"] != "PASS FOR REVIEW":
                raise HTTPException(409, "Validation blocks submission")
            update(r, status="in_review", submitted_at=now())
        else:
            if u["role"] != "reviewer" or u["username"] == r.data["author"]:
                raise HTTPException(403, "Independent reviewer required")
            if r.data["status"] != "in_review":
                raise HTTPException(409, "Submit the revision for review first")
            if body.action == "approve":
                result = run_validation(s, r, u["username"])
                if result["decision"] != "PASS FOR REVIEW":
                    raise HTTPException(409, "Validation blocks approval")
                a = dict(
                    hash=artwork_hash(r.data["fields"]),
                    source_version=r.data["source_version"],
                    ruleset=RULESET,
                    reviewer=u["username"],
                    timestamp=now(),
                    comment=body.comment,
                )
                update(r, status="approved", approval=a)
            else:
                update(r, status="rejected", approval=None, review_comment=body.comment)
        audit(
            s,
            "REVIEW_" + body.action.upper(),
            u["username"],
            dict(
                draft_id=id, hash=artwork_hash(r.data["fields"]), comment=body.comment
            ),
        )
        return out(r)


@app.get("/api/v1/drafts/{id}/artwork.{ext}")
def artwork(id: str, ext: str, u=Depends(user)):
    with Session() as s:
        r = get(s, id, "draft")
        fields = r.data["fields"]
        if ext == "svg":
            return RawResponse(svg(fields), media_type="image/svg+xml")
        if ext == "pdf":
            return RawResponse(
                pdf(fields),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="label-{id}.pdf"'
                },
            )
        raise HTTPException(404)


@app.post("/api/v1/drafts/{id}/release")
def release(id: str, u=Depends(user)):
    with lock, Session.begin() as s:
        r = get(s, id, "draft")
        if r.data["status"] != "approved":
            raise HTTPException(409, "Human approval required")
        revisions = [
            d for d in items(s, "draft") if d.data["label_id"] == r.data["label_id"]
        ]
        if r.data["label_revision"] != max(d.data["label_revision"] for d in revisions):
            raise HTTPException(
                409,
                "A newer artwork revision exists. Review the latest revision before release.",
            )
        result = run_validation(s, r, u["username"], True)
        if result["decision"] != "PASS FOR REVIEW":
            raise HTTPException(
                409, "Release blocked: stale approval, source or content"
            )
        summary = dict(
            product=r.data["fields"]["name"],
            variant=r.data["fields"]["variant"],
            label_revision=r.data["label_revision"],
            label_configuration=out(get(s, r.data["label_id"], "label")),
            source_id=r.data["source_id"],
            source_version=r.data["source_version"],
            validation=result,
            approval=r.data["approval"],
            artwork_hash=artwork_hash(r.data["fields"]),
            release_timestamp=now(),
            ruleset=RULESET,
            limitations="Educational synthetic prototype; configured checks only, not regulatory certification.",
        )
        rel = add(
            s,
            "release",
            dict(
                draft_id=id, summary=summary, fields=r.data["fields"], created_at=now()
            ),
        )
        update(r, status="released")
        audit(
            s,
            "RELEASE_CREATED",
            u["username"],
            dict(release_id=rel.id, artwork_hash=summary["artwork_hash"]),
        )
        # Changes close only when each affected label has a released revision at this source version.
        for ch in items(s, "change"):
            if ch.data["new_source_id"] == r.data["source_id"]:
                done = all(
                    any(
                        d.data["label_id"] == lid
                        and d.data["source_id"] == r.data["source_id"]
                        and d.data["status"] == "released"
                        for d in items(s, "draft")
                    )
                    for lid in ch.data["affected_labels"]
                )
                if done:
                    update(ch, status="completed")
        return out(rel)


@app.get("/api/v1/releases/{id}/download")
def download(id: str, u=Depends(user)):
    with Session() as s:
        r = get(s, id, "release")
        b = BytesIO()
        with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("label.svg", svg(r.data["fields"]))
            z.writestr("label.pdf", pdf(r.data["fields"]))
            z.writestr("release-summary.json", json.dumps(r.data["summary"], indent=2))
            doc = get(s, r.data["summary"]["source_id"], "document")
            z.writestr("source-evidence.json", json.dumps(out(doc), indent=2))
        return RawResponse(
            b.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="aegis-release-{id[:8]}.zip"'
            },
        )


class BenchmarkInput(Strict):
    change_id: str | None = None


@app.post("/api/v1/benchmarks")
def bench(body: BenchmarkInput | None = None, u=Depends(user)):
    with lock, Session.begin() as s:
        label = get(s, "label-cardiac-unit", "label")
        doc = current_source(s, label)
        changed = None
        if body and body.change_id:
            change = get(s, body.change_id, "change")
            changed = [x["field"] for x in change.data["changes"]]
            if change.data["affected_labels"]:
                label = get(s, change.data["affected_labels"][0], "label")
                doc = current_source(s, label)
        result = benchmark(
            expected_fields(doc, label), doc.data["source_revision"], changed
        )
        r = add(s, "benchmark", dict(**result, created_at=now()))
        audit(
            s,
            "MUTATION_SUITE_EXECUTED",
            u["username"],
            dict(run_id=r.id, detected=result["detected"], total=result["total"]),
        )
        return out(r)


@app.get("/api/v1/audit/verify")
def verify(u=Depends(user)):
    with Session() as s:
        return verify_chain(s)


@app.post("/api/v1/documents/upload")
async def upload(device_id: str, file: UploadFile = File(...), u=Depends(user)):
    raw = await file.read(10 * 1024 * 1024 + 1)
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "PDF limit is 10 MB")
    if not raw.startswith(b"%PDF-"):
        raise HTTPException(422, "Upload a PDF document")
    try:
        extracted = extract(raw)
        fields = extracted["fields"]
        evidence = extracted["evidence"]
        proposal = propose(fields, task="extract", text=extracted["text"])
        if proposal["mode"] == "ai-assisted":
            # A proposed source value must have literal supporting text, not just an LLM assertion.
            if all(v and v in extracted["text"] for v in proposal["fields"].values()):
                fields = proposal["fields"]
                for k, v in fields.items():
                    if k not in evidence or evidence[k]["quote"] != v:
                        page = next(
                            (
                                i + 1
                                for i, p in enumerate(
                                    fitz.open(stream=raw, filetype="pdf")
                                )
                                if v in p.get_text()
                            ),
                            None,
                        )
                        evidence[k] = dict(page=page, quote=v, bbox=None)
            else:
                proposal = {
                    **proposal,
                    "mode": "deterministic",
                    "provider_error": "AI extraction contained unsupported source values",
                }
    except ValueError as e:
        raise HTTPException(422, str(e))
    with lock, Session.begin() as s:
        get(s, device_id, "device")
        r = add(
            s,
            "document",
            dict(
                device_id=device_id,
                title=Path(file.filename or "uploaded.pdf").name[:150],
                status="candidate",
                source_revision=0,
                fields=fields,
                evidence=evidence,
                mode=proposal["mode"],
                provider_error=proposal["provider_error"],
                conflicts=extracted["conflicts"],
                contradiction=extracted["contradiction"],
                file_hash=hashlib.sha256(raw).hexdigest(),
                created_at=now(),
            ),
        )
        upload_root = Path(os.getenv("UPLOAD_DIR", "artifacts/uploads"))
        upload_root.mkdir(parents=True, exist_ok=True)
        (upload_root / (r.id + ".pdf")).write_bytes(raw)
        audit(
            s,
            "DOCUMENT_EXTRACTED",
            u["username"],
            dict(document_id=r.id, mode=proposal["mode"]),
        )
        return out(r)


@app.post("/api/v1/documents/{id}/approve")
def approve_document(id: str, u=Depends(user)):
    if u["role"] != "reviewer":
        raise HTTPException(403, "Reviewer must approve extracted source fields")
    with lock, Session.begin() as s:
        r = get(s, id, "document")
        if r.data["status"] != "candidate":
            raise HTTPException(409, "Document is not an unapproved candidate")
        if field_errors(r.data["fields"]):
            raise HTTPException(409, "; ".join(field_errors(r.data["fields"])))
        if r.data.get("contradiction"):
            raise HTTPException(
                409, "Conflicting source values require a corrected document"
            )
        if set(r.data["fields"]) != set(FIELDS):
            raise HTTPException(
                409, "All controlled fields required before source approval"
            )
        result = do_source(
            s,
            r.data["device_id"],
            r.data["fields"],
            r.data["title"],
            u["username"],
            r.data["evidence"],
        )
        update(r, status="processed")
        return result


@app.get("/api/v1/documents/{id}/pdf")
def source_pdf(id: str, u=Depends(user)):
    with Session() as s:
        d = get(s, id, "document")
        stored = Path(os.getenv("UPLOAD_DIR", "artifacts/uploads")) / (d.id + ".pdf")
        if stored.exists():
            return FileResponse(
                stored, media_type="application/pdf", filename="source-document.pdf"
            )
        return RawResponse(
            pdf(d.data["fields"]),
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="synthetic-source.pdf"'},
        )


# Put the guard outside route middleware so rejections retain security headers.
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        host.strip()
        for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        if host.strip()
    ],
)
app.add_middleware(RequestGuard)

front = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if front.exists():
    app.mount("/assets", StaticFiles(directory=front / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "API route not found")
        return FileResponse(front / "index.html")
