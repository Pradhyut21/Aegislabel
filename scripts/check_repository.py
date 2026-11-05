"""Inspect exactly the files Git could publish; never inspect ignored user secrets."""

import re
import subprocess
from pathlib import Path

PATTERNS = {
    "GitHub credential": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
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
        if forbidden:
            errors.append(f"Private/generated artifact selected: {relative}")
            continue
        data = path.read_bytes()
        total += len(data)
        if len(data) > 1_000_000:
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
