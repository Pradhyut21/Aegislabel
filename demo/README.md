# AegisLabel-FX narrated real-app demo

A **2 minute 21 second** walkthrough of the actual local application: change a warning, introduce a faulty draft, observe the deterministic block, correct it, obtain independent human-role approval, download a release ZIP, run 24 mutations, and inspect the audit chain.

This follows the [BRAG](https://github.com/latent-spaces/brag) inspect → plan → compose → review workflow, with a documented length exception for the complete safety workflow. BRAG is tooling guidance, not the application author. Real Playwright footage is used; result screens are not recreated as animation. Source claims and deliberate exceptions are recorded in [brag-plan.md](brag-plan.md).

**Voice disclosure:** narration is synthetic Kokoro `af_heart`, generated locally through Hyperframes. It is not a recording of a human or a cloned person. No paid audio/video service, stock footage, stock music or public app deployment is used. The application runs in clearly labeled deterministic mode. No live Meta model inference is claimed.

## Reproduce (Linux commands)

Start with the root README installation and a built frontend. Install the optional media tools separately; none is required to run the application:

```bash
npm ci --prefix demo
python -m venv .venv-media
.venv-media/bin/pip install -r demo/requirements.txt
mkdir -p artifacts/demo artifacts/hyperframes-cache/tts/models artifacts/hyperframes-cache/tts/voices
```

Local TTS needs approximately 354 MB of model/voice files, plus packages and render space. Download `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the [official kokoro-onnx model release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0) into `artifacts/hyperframes-cache/tts/models/` and `.../voices/` respectively. Review [third-party notices](../THIRD_PARTY_NOTICES.md). These files must never be committed. On Windows, keep these paths and package caches on D:; adapt `.venv*/bin/python` to `.venv*/Scripts/python.exe` in the narration script. No Docker media build is needed.

Generate narration, then start an **unused isolated synthetic database** (do not reuse a changed DB for a fresh take):

```bash
python demo/generate_narration.py
AI_ENABLED=false DATABASE_URL=sqlite:///./artifacts/demo-fresh.db .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8002
# In another terminal:
node demo/capture.mjs
python demo/build_composition.py
```

The recorder asserts the actual warning block, disabled review submission, corrected validation, approval, ZIP download and mutation results. It produces measured scene timings in `artifacts/demo/capture.json`; these drive the final timeline rather than an invented screen sequence. The public FDA sample has its own explanatory scene, separate from application footage.

Render locally after checking and inspecting snapshots:

```bash
export HYPERFRAMES_BROWSER_PATH="$(node --input-type=module -e "import{chromium}from'./demo/node_modules/playwright/index.mjs';console.log(chromium.executablePath())")"
export HYPERFRAMES_CACHE_DIR="$PWD/artifacts/hyperframes-cache"
export TMPDIR="$PWD/artifacts/demo"
cd demo/composition
../node_modules/.bin/hyperframes preview --background
../node_modules/.bin/hyperframes preview --status
npm run check
../node_modules/.bin/hyperframes snapshot --at 3,47,74,95,116,132
../node_modules/.bin/hyperframes render --quality delivery --fps 30 --workers 1 --frames-cache-dir off --output ../../artifacts/demo/AegisLabel-FX-demo.mp4
../node_modules/.bin/hyperframes preview --stop
```

If Playwright's browser is unavailable, install the version matching the pinned Playwright package first. Renderer checks may take several minutes. Media assets, models, database, private runtime output and editor history are ignored by Git. All source scripts, narration, design, pinned media dependencies and composition HTML remain reviewable. The separate media toolchain pins `undici` 7.30.1 to remediate its upstream dependency advisory.

## Submission limits

The event's public page does not expose a video limit. This complete cut is **not claimed to meet an unverified submission duration**. The published November 4 deadline has passed. See [hackathon assessment](../docs/HACKATHON_ASSESSMENT.md) before attempting a submission.
