"""Bounded deterministic extraction with exact document evidence."""

import fitz
from .domain import FIELDS, field_errors


def extract(raw):
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("PDF limit is 10 MB")
    if not raw.startswith(b"%PDF-"):
        raise ValueError("Upload a PDF document")
    try:
        doc = fitz.open(stream=raw, filetype="pdf")
    except Exception:
        raise ValueError("Malformed PDF")
    with doc:
        if doc.is_encrypted or len(doc) > 100:
            raise ValueError("Encrypted PDF or more than 100 pages")
        pages = [p.get_text() for p in doc]
        text = "\n".join(pages)
        if len(text) > 250000:
            raise ValueError("Extracted text exceeds limit")
        if not text.strip():
            raise ValueError("No extractable text. OCR is not configured.")
        fields = {}
        evidence = {}
        conflicts = []
        for i, page in enumerate(doc):
            for line in pages[i].splitlines():
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k = k.strip().lower()
                v = v.strip()
                if k in FIELDS and v:
                    if len(v) > 240:
                        raise ValueError(f"{k} exceeds 240 characters")
                    if k in fields and fields[k] != v:
                        conflicts.append(
                            dict(field=k, first=fields[k], conflicting=v, page=i + 1)
                        )
                        continue
                    fields[k] = v
                    evidence[k] = dict(
                        page=i + 1,
                        quote=v,
                        bbox=list(page.search_for(v)[0])
                        if page.search_for(v)
                        else None,
                    )
        if not fields:
            raise ValueError("No controlled fields found. Use field: value lines.")
        if field_errors(fields):
            raise ValueError("; ".join(field_errors(fields)))
        return dict(
            fields=fields,
            evidence=evidence,
            conflicts=conflicts,
            contradiction=bool(conflicts),
            text=text,
        )


def generated_evidence(fields):
    """Locate each synthetic field in the actual generated source PDF."""
    from .domain import pdf

    result = {}
    with fitz.open(stream=pdf(fields), filetype="pdf") as document:
        for key, value in fields.items():
            matches = [
                (page.number + 1, list(box))
                for page in document
                for box in page.search_for(str(value))
            ]
            result[key] = dict(
                page=matches[0][0] if matches else None,
                quote=value,
                bbox=matches[0][1] if matches else None,
                locations=matches,
            )
    return result
