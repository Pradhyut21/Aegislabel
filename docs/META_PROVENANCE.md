# Meta technology provenance and hackathon claims

The application was implemented with OpenAI Codex assistance. It must not be described as authored, sponsored, certified or endorsed by Meta.

| Technology | Actual use | Verification |
| --- | --- | --- |
| React (`react`, `react-dom`) | Main application interface; React originated at Facebook/Meta and is now maintained as an open-source project | Compiled, browser-tested application; pinned dependencies in `frontend/package.json` |
| Official Meta Llama API Python SDK (`llama-api-client`) | Native server-side adapter in `backend/meta_provider.py`; JSON-schema output, bounded response streaming, timeouts and bounded SDK retries | Native request/response and fallback paths tested using mocked HTTP through the actual SDK |
| Current Meta Model API | `AI_PROVIDER=meta-model`, official `https://api.meta.ai/v1/chat/completions`, `MODEL_API_KEY`, configurable `MODEL_API_MODEL` (default `muse-spark-1.3`) | Official endpoint/key routing and truncated-response failure paths tested with mocked HTTP |
| Meta/Llama inference | Optional only: `AI_PROVIDER=meta`, `AI_ENABLED=true`, `LLAMA_API_KEY` and `LLAMA_MODEL` | **No live Meta inference has been executed in this environment.** Recorded demo and baseline benchmarks use deterministic mode. |

The native adapter uses Meta's actual `completion_message` response format and official JSON-schema request format. This is distinct from the separate OpenAI-compatible adapter. AI-generated fields still face the same deterministic checks, source-evidence controls and independent reviewer gate. No model can approve a label.

## Enable genuine Meta inference, if authorized

Install the locked dependencies, obtain authorized access through Meta's official Llama API, and set these **server environment variables**:

```text
AI_ENABLED=true
AI_PROVIDER=meta
LLAMA_API_KEY=<configure securely; never commit or paste into chat>
LLAMA_MODEL=<a model actually available to your account>
LLAMA_API_BASE_URL=https://api.llama.com/v1
```

Setting `AI_ENABLED=true` is an explicit opt-in to potential external API charges. No paid service is enabled by default. Model availability, account access and provider terms must be verified separately. When the service is absent or its output fails schema validation, outputs are labeled deterministic with a fallback reason.

A dependency or compatible adapter alone does not prove that a hackathon's required model was used. If its rules require Meta inference, capture an actual authorized run and its model/provider metadata before claiming compliance. See [the verified hackathon assessment](HACKATHON_ASSESSMENT.md): the published deadline has passed, and detailed eligibility, synthetic-data policy and video limit remain unverified. Winning or eligibility cannot be guaranteed.

References: https://github.com/meta-llama/llama-api-python and https://llama.developer.meta.com/docs.

For the current Meta Model API, use `AI_PROVIDER=meta-model`, `MODEL_API_KEY`, and `MODEL_API_MODEL` with explicit `AI_ENABLED=true`. The official 2026 quickstart is https://dev.meta.ai/docs/quickstart. This mode uses the existing bounded HTTP transport; the legacy Llama SDK is a separate optional adapter.
