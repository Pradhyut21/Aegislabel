"""Export the actual server contract without enabling external AI."""

import json
from pathlib import Path
from backend.main import app

Path("docs/openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n")
print("Wrote docs/openapi.json")
