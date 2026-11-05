"""Generate the requested local Kokoro narration through BRAG's Hyperframes route."""

import json
import os
import subprocess
import wave
from pathlib import Path

root = Path(__file__).resolve().parents[1]
scenes = json.loads((root / "demo/narration.json").read_text())
assets = root / "demo/composition/assets"
assets.mkdir(exist_ok=True, parents=True)
env = {
    **os.environ,
    "HYPERFRAMES_PYTHON": str(root / ".venv-media/bin/python"),
    "HYPERFRAMES_CACHE_DIR": str(root / "artifacts/hyperframes-cache"),
    "TMPDIR": str(root / "artifacts/demo"),
}
for scene in scenes:
    target = assets / (scene["id"] + ".wav")
    if not target.exists():
        script = assets / (scene["id"] + ".txt")
        script.write_text(scene["text"])
        subprocess.run(
            [
                "npx",
                "hyperframes",
                "tts",
                str(script),
                "--voice",
                "af_heart",
                "--speed",
                "1.0",
                "--output",
                str(target),
                "--json",
            ],
            cwd=root / "demo",
            env=env,
            check=True,
        )
    with wave.open(str(target), "rb") as audio:
        scene["speech_duration"] = audio.getnframes() / audio.getframerate()
    scene["duration"] = round(scene["speech_duration"] + 1.0, 3)
    print(scene["id"], scene["duration"], flush=True)
(root / "artifacts/demo/scenes.json").write_text(json.dumps(scenes, indent=2))
print("Total planned seconds:", sum(s["duration"] for s in scenes))
