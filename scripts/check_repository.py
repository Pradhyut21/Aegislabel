"""Inspect exactly the files Git could publish; never inspect ignored user secrets."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

REVIEWED_EXPORTS = {
    "demo/media/AegisLabel-FX-demo.mp4": 20_000_000,
    "demo/media/release-package.zip": 100_000,
}

PATTERNS = {
    "GitHub credential": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "Fine-grained GitHub credential": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    "Provider secret": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b"),
    "AWS access identifier": re.compile(rb"\bAKIA[A-Z0-9]{16}\b"),
    "Private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def main():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    paths = sorted(set(result.stdout.decode().strip("\0").split("\0")))
    errors = []
    total = 0
    for relative in paths:
        if not relative:
            continue
        path = root / relative
        if not path.exists():
            continue
        if path.is_symlink():
            errors.append(f"Symlink requires explicit review: {relative}")
            continue
        forbidden = any(
            part in {".venv", "node_modules", "test-results", "uploads"}
            for part in path.relative_to(root).parts
        )
        forbidden |= path.suffix.lower() in {
            ".db",
            ".sqlite",
            ".sqlite3",
            ".pem",
            ".key",
            ".p12",
            ".zip",
        }
        forbidden |= path.name.startswith(".env") and path.name != ".env.example"
        forbidden |= (
            relative.startswith("artifacts/") and relative != "artifacts/.gitkeep"
        )
        reviewed_export = relative in REVIEWED_EXPORTS
        if reviewed_export:
            manifest = json.loads((root / "demo/media/demo-manifest.json").read_text())
            expected = manifest["files"][path.name]
            if (
                path.stat().st_size > REVIEWED_EXPORTS[relative]
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]
            ):
                errors.append(
                    f"Reviewed demo export failed size/hash verification: {relative}"
                )
            forbidden = False
        if forbidden:
            errors.append(f"Private/generated artifact selected: {relative}")
            continue
        data = path.read_bytes()
        if not reviewed_export:
            total += len(data)
        if len(data) > 1_000_000 and not reviewed_export:
            errors.append(f"Unexpected large file: {relative}")
        for title, pattern in PATTERNS.items():
            if pattern.search(data):
                errors.append(f"{title} pattern in {relative}")
    if total > 4_000_000:
        errors.append("Source bundle exceeds 4 MB; review generated files")
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"Repository check passed: {len(paths)} files, {total:,} bytes; no disallowed artifacts or recognized credential patterns."
    )


if __name__ == "__main__":
    main()
