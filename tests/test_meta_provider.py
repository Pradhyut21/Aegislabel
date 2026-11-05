import json
import httpx
from backend.domain import FIELDS
from backend.provider import propose, enabled


def configure(monkeypatch):
    for key, value in {
        "AI_ENABLED": "true",
        "AI_PROVIDER": "meta",
        "LLAMA_API_KEY": "mock",
        "LLAMA_MODEL": "test-model",
        "LLAMA_API_BASE_URL": "https://example.invalid/v1",
    }.items():
        monkeypatch.setenv(key, value)


def test_native_meta_sdk_request_and_response(monkeypatch):
    configure(monkeypatch)
    fields = {key: "approved" for key in FIELDS}
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        assert body["model"] == "test-model"
        assert body["response_format"]["type"] == "json_schema"
        assert body["max_completion_tokens"] == 2200
        return httpx.Response(
            200,
            json={
                "completion_message": {
                    "role": "assistant",
                    "content": {"type": "text", "text": json.dumps({"fields": fields})},
                    "stop_reason": "stop",
                },
                "metrics": [
                    {"metric": "num_output_tokens", "value": 30, "unit": "tokens"}
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = propose(fields, client=client)
    assert result["mode"] == "ai-assisted" and result["provider"] == "meta-llama-api"
    assert result["usage"][0]["value"] == 30 and len(requests) == 1


def test_missing_native_key_does_not_call_provider(monkeypatch):
    configure(monkeypatch)
    monkeypatch.delenv("LLAMA_API_KEY")
    assert not enabled() and propose({})["mode"] == "deterministic"


def test_incomplete_or_invalid_meta_response_falls_back(monkeypatch):
    configure(monkeypatch)
    for response in [
        {
            "completion_message": {
                "role": "assistant",
                "content": "{}",
                "stop_reason": "length",
            }
        },
        {"choices": []},
    ]:
        with httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=response)
            )
        ) as client:
            result = propose({}, client=client)
        assert result["mode"] == "deterministic" and result["provider_error"]


def test_current_meta_model_api_uses_official_endpoint_and_key(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "meta-model")
    monkeypatch.setenv("MODEL_API_KEY", "mock-model-key")
    fields = {key: "approved" for key in FIELDS}

    def handler(request):
        assert str(request.url) == "https://api.meta.ai/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer mock-model-key"
        assert json.loads(request.content)["model"] == "muse-spark-1.3"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps({"fields": fields})},
                    }
                ]
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = propose(fields, client=client)
    assert result["provider"] == "meta-model-api" and result["mode"] == "ai-assisted"


def test_current_meta_model_api_rejects_truncated_output(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "meta-model")
    monkeypatch.setenv("MODEL_API_KEY", "mock")
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "choices": [
                        {"finish_reason": "length", "message": {"content": "{}"}}
                    ]
                },
            )
        )
    ) as client:
        assert propose({}, client=client)["mode"] == "deterministic"
