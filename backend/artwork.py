"""One SVG renderer is used for previews, hashes and release packages."""

import html
import textwrap
from reportlab.graphics.barcode import createBarcodeDrawing


def render_svg(fields):
    def esc(value):
        return html.escape(str(value))

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="520" height="650" viewBox="0 0 520 650"><rect x="1" y="1" width="518" height="648" rx="5" fill="white" stroke="#CBD5E1"/><g font-family="Arial,sans-serif" fill="#10263F">'
    ]

    def text(x, y, value, size=12, color="#10263F", weight="normal"):
        size = min(size, 460 / max(1, len(str(value)) * 0.65))
        parts.append(
            f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{esc(value)}</text>'
        )

    text(26, 33, "AEGIS SYNTHETIC DEVICES", 10, "#64748B", "bold")
    parts.append('<path d="M26 48H494" stroke="#CBD5E1"/>')
    y = 80
    for line in textwrap.wrap(fields.get("name", ""), 37):
        text(26, y, line, 21, weight="bold")
        y += 25
    text(26, y + 7, "REF " + fields.get("identifier", ""), 14, weight="bold")
    y += 32
    text(26, y, fields.get("variant", "") + " / " + fields.get("packaging", ""), 12)
    y += 26
    parts.append(
        f'<rect x="22" y="{y - 14}" width="476" height="58" rx="3" fill="#F8FAFC" stroke="#E2E8F0"/>'
    )
    for line in textwrap.wrap(fields.get("warning", ""), 66):
        text(30, y + 3, line, 12, weight="bold")
        y += 16
    y = max(y + 27, 250)
    for k in [
        "sterilization",
        "market",
        "language",
        "ifu",
        "symbols",
        "claims",
        "translation",
        "manufacturer",
    ]:
        v = fields.get(k, "")
        lines = textwrap.wrap(f"{k.upper()}: {v}", 79) or [""]
        for line in lines:
            text(26, y, line, 10)
            y += 15
        y += 5
    barcode = createBarcodeDrawing(
        "Code128",
        value=fields.get("barcode", "") or "EMPTY",
        barHeight=32,
        barWidth=1.0,
        humanReadable=False,
    )
    b = barcode.asString("svg")
    b = b[b.index("<svg") :]
    b = b.replace("<svg ", f'<svg x="26" y="{max(y + 5, 515)}" ', 1)
    parts.append(b)
    y = max(y + 5, 515) + 60
    text(26, y, "BARCODE: " + fields.get("barcode", ""), 10)
    text(26, y + 17, "UDI-DI: " + fields.get("udi", ""), 10)
    parts.append(f'<path d="M26 {y + 36}H494" stroke="#CBD5E1"/>')
    text(
        26,
        y + 57,
        "SYNTHETIC / EDUCATIONAL PROTOTYPE / NOT FOR CLINICAL USE",
        9,
        "#64748B",
    )
    parts.append("</g></svg>")
    height = max(650, y + 75)
    return (
        "".join(parts)
        .replace(
            'height="650" viewBox="0 0 520 650"',
            f'height="{height}" viewBox="0 0 520 {height}"',
        )
        .replace('height="648"', f'height="{height - 2}"')
    )
