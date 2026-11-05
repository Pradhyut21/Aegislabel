"""Generate small, actual PDF specifications for the upload demo."""

from pathlib import Path
import json
from backend.domain import pdf

root = Path("sample-data")
root.mkdir(exist_ok=True)
fields = dict(
    name="Sterile Cardiac Procedure Kit",
    identifier="CK-240",
    variant="Standard",
    udi="09506000134305",
    barcode="09506000134305",
    warning="Do not reuse.",
    ifu="IFU-CK-240 / R1",
    packaging="Unit pouch",
    symbols="Single use; Consult IFU",
    claims="Approved intended use only",
    language="en",
    translation="Do not reuse.",
    manufacturer="Aegis Synthetic Devices Ltd.",
    sterilization="Sterile",
    market="EU",
)
for version in [1, 2]:
    if version == 2:
        fields = {
            **fields,
            "warning": "Do not reuse. Inspect packaging before use.",
            "translation": "Do not reuse. Inspect packaging before use.",
        }
    (root / f"cardiac-spec-r{version}.pdf").write_bytes(pdf(fields))
    (root / f"cardiac-spec-r{version}.json").write_text(
        json.dumps(fields, indent=2) + "\n"
    )
print("Generated two synthetic specification PDFs and field snapshots.")
