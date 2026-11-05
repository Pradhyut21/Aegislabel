"""Exercise hostile HTTP boundaries and provider streams, not just UI behavior."""

import asyncio
import json
import httpx
from backend.security import RequestGuard
from backend.provider import propose
from backend.domain import FIELDS


def test_untrusted_host_and_rejection_headers(client):
    r = client.get("/api/v1/health", headers={"host": "attacker.example"})
    assert r.status_code == 400
    assert r.headers["x-frame-options"] == "DENY"
    r = client.post("/api/v1/benchmarks", headers={"x-csrf-token": "invalid"})
    assert r.status_code == 403
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"


def test_workspace_does_not_disclose_accounts_or_sessions(client):
    workspace = client.get("/api/v1/workspace").json()
    assert "user" not in workspace and "session" not in workspace
    assert "password_hash" not in json.dumps(workspace)
    assert "csrf" not in json.dumps(workspace)


def test_signout_revokes_server_session(client):
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/workspace").status_code == 401


def test_chunked_body_limit_without_content_length():
    reached = []
    responses = []
    chunks = iter(
        [
            {"type": "http.request", "body": b"1234", "more_body": True},
            {"type": "http.request", "body": b"5678", "more_body": False},
        ]
    )

    async def app(scope, receive, send):
        reached.append(True)

    async def receive():
        return next(chunks)

    async def send(message):
        responses.append(message)

    asyncio.run(
        RequestGuard(app, max_bytes=6)(
            {
                "type": "http",
                "path": "/api/v1/changes",
                "method": "POST",
                "headers": [],
            },
            receive,
            send,
        )
    )
    assert not reached
    start = next(r for r in responses if r["type"] == "http.response.start")
    assert start["status"] == 413
    assert dict(start["headers"])[b"x-content-type-options"] == b"nosniff"


def test_body_read_deadline_and_busy_limit():
    async def run(max_readers, slow=False):
        responses = []

        async def app(scope, receive, send):
            raise AssertionError("Rejected request reached app")

        async def receive():
            await asyncio.sleep(0.1)
            return {"type": "http.request", "body": b"x"}

        async def send(message):
            responses.append(message)

        guard = RequestGuard(app, read_timeout=0.001, max_readers=max_readers)
        await guard(
            {
                "type": "http",
                "path": "/api/v1/changes",
                "method": "POST",
                "headers": [],
            },
            receive,
            send,
        )
        return responses[0]["status"]

    assert asyncio.run(run(8)) == 408
    assert asyncio.run(run(0)) == 503


def test_provider_stops_reading_oversized_response(monkeypatch):
    for key, value in {
        "AI_ENABLED": "true",
        "AI_API_KEY": "mock",
        "AI_BASE_URL": "https://example.invalid/v1",
        "AI_MODEL": "test",
    }.items():
        monkeypatch.setenv(key, value)
    consumed = []

    class LargeStream(httpx.SyncByteStream):
        def __iter__(self):
            for _ in range(100):
                consumed.append(1)
                yield b"x" * 8192

    with httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, stream=LargeStream())
        )
    ) as client:
        result = propose({key: "approved" for key in FIELDS}, client=client)
    assert result["mode"] == "deterministic" and result["provider_error"]
    assert len(consumed) < 100
