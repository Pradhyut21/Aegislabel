import httpx
from backend.provider import propose
from backend.domain import FIELDS


def test_no_key_no_network(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    assert propose({})["mode"] == "deterministic"


def test_opt_in_required(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "test")
    monkeypatch.setenv("AI_ENABLED", "false")
    assert propose({})["mode"] == "deterministic"


def test_mock_success_invalid_and_timeout(monkeypatch):
    import json

    for k, v in {
        "AI_ENABLED": "true",
        "AI_API_KEY": "mock",
        "AI_BASE_URL": "https://example.invalid/v1",
        "AI_MODEL": "meta-test",
    }.items():
        monkeypatch.setenv(k, v)
    f = {k: "approved" for k in FIELDS}

    def handler(r):
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps({"fields": f})}}],
                "usage": {"total_tokens": 30},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        assert propose(f, client=c)["mode"] == "ai-assisted"
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"bad": "output"})
        )
    ) as c:
        p = propose(f, client=c)
        assert p["mode"] == "deterministic" and p["provider_error"]
    calls = []

    def timeout(r):
        calls.append(1)
        raise httpx.ReadTimeout("test")

    with httpx.Client(transport=httpx.MockTransport(timeout)) as c:
        assert propose(f, client=c)["mode"] == "deterministic"
    assert len(calls) == 3
