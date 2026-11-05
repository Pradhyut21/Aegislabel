"""Normalize measured audio, export a real first-frame poster and hash deliverables."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/demo"
video = OUT / "AegisLabel-FX-demo.mp4"


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


measurement = run(
    [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(video),
        "-af",
        "loudnorm=I=-16:TP=-1:LRA=11:print_format=json",
        "-f",
        "null",
        "-",
    ]
).stderr
loudness = json.loads(measurement[measurement.rfind("{") :])
(OUT / "loudness-before.json").write_text(json.dumps(loudness, indent=2))
filter_value = (
    "loudnorm=I=-16:TP=-1:LRA=11:linear=true:"
    f"measured_I={loudness['input_i']}:measured_TP={loudness['input_tp']}:"
    f"measured_LRA={loudness['input_lra']}:measured_thresh={loudness['input_thresh']}:"
    f"offset={loudness['target_offset']}:print_format=json"
)
normalized = OUT / "normalized.mp4"
result = run(
    [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-i",
        str(video),
        "-c:v",
        "copy",
        "-af",
        filter_value,
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
        "-metadata",
        "comment=Actual AegisLabel-FX capture; synthetic workspace; AI-generated Kokoro narration; deterministic mode; educational prototype.",
        str(normalized),
    ]
)
normalized.replace(video)
(OUT / "loudness-normalization.txt").write_text(result.stderr)
probe = json.loads(
    run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(video),
        ]
    ).stdout
)
(OUT / "ffprobe.json").write_text(json.dumps(probe, indent=2))
run(
    [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-update",
        "1",
        str(OUT / "AegisLabel-FX-poster.jpg"),
    ]
)
shutil.copyfile(ROOT / "demo/transcript.vtt", OUT / "AegisLabel-FX-transcript.vtt")
files = [
    video,
    OUT / "AegisLabel-FX-poster.jpg",
    OUT / "AegisLabel-FX-transcript.vtt",
    OUT / "release-package.zip",
]
manifest = {
    "source_commit": run(["git", "rev-parse", "HEAD"]).stdout.strip(),
    "duration_seconds": float(probe["format"]["duration"]),
    "narration": "AI-generated Kokoro af_heart; not a human recording",
    "mode": "deterministic",
    "footage": "Real Playwright browser capture; scripted author/reviewer role demonstration in an isolated synthetic workspace",
    "public_reference_data": "Separate openFDA UDI + classification sample; not release evidence or benchmark ground truth",
    "files": {
        p.name: {
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in files
    },
}
(OUT / "demo-manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
