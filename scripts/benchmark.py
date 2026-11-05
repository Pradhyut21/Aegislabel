"""Reproducible pure benchmark; does not modify the application database."""

import json
from pathlib import Path
from backend.domain import FIELDS, benchmark

f = {k: "controlled-" + k for k in FIELDS}
f["warning"] = "Do not reuse. Inspect packaging before use."
result = benchmark(f, 2)
Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/benchmark.json").write_text(json.dumps(result, indent=2))
print(
    f"{result['detected']}/{result['total']} faults detected; {result['false_blocks']}/{result['clean_controls']} clean cases blocked"
)
