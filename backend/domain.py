"""Pure, bounded demonstration rules. No regulatory completeness is implied."""

import hashlib
import json
import html
import copy
import time
from io import BytesIO
from reportlab.graphics.barcode import code128

RULESET = "FX-2026.1"
FIELDS = {
    "name": "PRODUCT_NAME",
    "identifier": "DEVICE_IDENTIFIER",
    "variant": "VARIANT",
    "udi": "UDI_DI",
    "barcode": "BARCODE_CONTENT",
    "warning": "SAFETY_WARNING",
    "ifu": "IFU_REVISION",
    "packaging": "PACKAGING_LEVEL",
    "symbols": "CONTROLLED_SYMBOLS",
    "claims": "APPROVED_CLAIMS",
    "language": "CONTROLLED_LANGUAGE",
    "translation": "CONTROLLED_TRANSLATION",
    "manufacturer": "MANUFACTURER",
    "sterilization": "STERILIZATION",
    "market": "MARKET",
}


FIELD_LIMITS = {
    "name": 100,
    "identifier": 40,
    "variant": 40,
    "udi": 40,
    "barcode": 32,
    "warning": 240,
    "ifu": 60,
    "packaging": 40,
    "symbols": 120,
    "claims": 200,
    "language": 8,
    "translation": 240,
    "manufacturer": 100,
    "sterilization": 40,
    "market": 10,
}


def field_errors(fields):
    errors = [
        f"{key} exceeds {FIELD_LIMITS[key]} characters"
        for key, value in fields.items()
        if key in FIELD_LIMITS and len(value) > FIELD_LIMITS[key]
    ]
    barcode = fields.get("barcode", "")
    if barcode and any(ord(c) < 32 or ord(c) > 126 for c in barcode):
        errors.append("Barcode must use printable ASCII characters")
    return errors


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(x):
    return hashlib.sha256(
        (x if isinstance(x, bytes) else canonical(x).encode())
    ).hexdigest()


def svg(fields):
    from .artwork import render_svg

    return render_svg(fields)


def artwork_hash(fields):
    return hashlib.sha256(svg(fields).encode()).hexdigest()


def pdf(fields):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    b = BytesIO()
    doc = SimpleDocTemplate(
        b, pagesize=(720, 650), topMargin=25, bottomMargin=25, invariant=1
    )
    style = getSampleStyleSheet()
    story = [Paragraph("AegisLabel-FX / Synthetic Device Label", style["Title"])]
    for k in FIELDS:
        story.append(
            Paragraph(
                html.escape(k.upper() + ": " + str(fields.get(k, ""))), style["Normal"]
            )
        )
        story.append(Spacer(1, 7))
    story.append(
        code128.Code128(
            str(fields.get("barcode", "")) or "EMPTY", barHeight=30, barWidth=1.0
        )
    )
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "SYNTHETIC / Educational prototype / Not for clinical use", style["Normal"]
        )
    )
    doc.build(story)
    return b.getvalue()


def validate(
    fields,
    expected,
    version,
    source_version,
    approval=None,
    require_approval=False,
    contradiction=False,
):
    findings = []
    for key, rule in FIELDS.items():
        ok = fields.get(key) == expected.get(key)
        findings.append(
            dict(
                rule_id="FX-" + rule,
                field=key,
                expected=expected.get(key),
                observed=fields.get(key),
                severity="critical" if not ok else "info",
                source_reference=f"SPEC / revision {source_version} / {key}",
                reason_code=rule + ("_MATCH" if ok else "_MISMATCH"),
                passed=ok,
            )
        )
    for rule, ok, exp, obs in [
        ("SOURCE_VERSION", version == source_version, source_version, version),
        ("SOURCE_CONTRADICTION", not contradiction, False, contradiction),
    ]:
        findings.append(
            dict(
                rule_id="FX-" + rule,
                field=rule.lower(),
                expected=exp,
                observed=obs,
                severity="critical" if not ok else "info",
                source_reference=f"SPEC / revision {source_version}",
                reason_code=rule + ("_MATCH" if ok else "_MISMATCH"),
                passed=ok,
            )
        )
    if require_approval:
        ok = bool(
            approval
            and approval.get("hash") == artwork_hash(fields)
            and approval.get("source_version") == source_version
            and approval.get("ruleset") == RULESET
        )
        findings.append(
            dict(
                rule_id="FX-APPROVAL_BINDING",
                field="approval",
                expected=artwork_hash(fields),
                observed=(approval or {}).get("hash"),
                severity="critical" if not ok else "info",
                source_reference="Reviewer record",
                reason_code="APPROVAL_VALID" if ok else "APPROVAL_STALE_OR_MISSING",
                passed=ok,
            )
        )
    decision = (
        "BLOCKED"
        if any(
            not f["passed"] and f["rule_id"] != "FX-SOURCE_CONTRADICTION"
            for f in findings
        )
        else "ESCALATE"
        if contradiction
        else "PASS FOR REVIEW"
    )
    return dict(
        decision=decision,
        findings=findings,
        ruleset=RULESET,
        artwork_hash=artwork_hash(fields),
    )


SCENARIOS = [
    ("Wrong device identifier", "identifier", "WRONG-001"),
    ("Missing device identifier", "identifier", ""),
    ("Wrong UDI", "udi", "00000000000000"),
    ("Corrupt barcode", "barcode", "BAD-CODE"),
    ("Missing warning", "warning", ""),
    ("Warning regression", "warning", "Do not reuse."),
    ("Partial warning", "warning", "Inspect packaging before use."),
    ("Wrong IFU", "ifu", "IFU-001 / R0"),
    ("Wrong variant", "variant", "Pediatric"),
    ("Wrong packaging", "packaging", "Shipping carton"),
    ("Missing symbols", "symbols", ""),
    ("Unsupported symbol", "symbols", "CE-UNAPPROVED"),
    ("Unsupported claim", "claims", "Guaranteed safe"),
    ("Missing manufacturer", "manufacturer", ""),
    ("Wrong sterilization", "sterilization", "Non-sterile"),
    ("Wrong market", "market", "JP"),
    ("Wrong language", "language", "zz"),
    ("Wrong translation", "translation", "Reuse permitted"),
    ("Missing product name", "name", ""),
    ("Old source version", "_source", 0),
    ("Stale artwork approval", "_approval", "oldhash"),
    ("Stale source approval", "_approval_source", 0),
    ("Contradictory sources", "_conflict", True),
    ("Absent approval", "_noapproval", True),
]


def benchmark(expected, source_version, changed_fields=None):
    rows = []
    correct = copy.deepcopy(expected)
    # Guarantee warning-regression mutants differ even when the initial fixture is R1.
    correct["warning"] = "Do not reuse. Inspect packaging before use."
    selected = (
        targeted_scenarios(changed_fields) if changed_fields is not None else SCENARIOS
    )
    for title, key, value in selected:
        f = copy.deepcopy(correct)
        v = source_version
        conflict = False
        approval = dict(hash=artwork_hash(f), source_version=v, ruleset=RULESET)
        if key == "_source":
            v = 0
        elif key == "_approval":
            approval["hash"] = value
        elif key == "_approval_source":
            approval["source_version"] = 0
        elif key == "_noapproval":
            approval = None
        elif key == "_conflict":
            conflict = True
        else:
            f[key] = value
        if not key.startswith("_approval") and key != "_noapproval":
            approval["hash"] = artwork_hash(f)
        start = time.perf_counter()
        result = validate(f, correct, v, source_version, approval, True, conflict)
        failed = [x["rule_id"] for x in result["findings"] if not x["passed"]]
        # Artwork baseline only sees visible content changes, not evidence or approval validity.
        artwork_detected = svg(f) != svg(correct)
        content = validate(f, correct, source_version, source_version)
        rows.append(
            dict(
                scenario=title,
                mutation=f"{key} → {value}",
                expected_detection=True,
                actual_detection=bool(failed),
                result="DETECTED" if failed else "ESCAPED",
                rules=failed,
                execution_ms=round((time.perf_counter() - start) * 1000, 3),
                artwork_detected=artwork_detected,
                rules_detected=content["decision"] == "BLOCKED",
            )
        )
    controls = []
    for _ in range(5):
        a = dict(
            hash=artwork_hash(correct), source_version=source_version, ruleset=RULESET
        )
        controls.append(
            validate(correct, correct, source_version, source_version, a, True)[
                "decision"
            ]
            == "BLOCKED"
        )
    baseline_clean = {
        "artwork": sum(svg(copy.deepcopy(correct)) != svg(correct) for _ in range(5)),
        "rules": sum(
            validate(copy.deepcopy(correct), correct, source_version, source_version)[
                "decision"
            ]
            != "PASS FOR REVIEW"
            for _ in range(5)
        ),
    }
    return dict(
        selection="change-targeted"
        if changed_fields is not None
        else "full-regression",
        changed_fields=changed_fields,
        impact=impact_experiment(),
        baseline_false_blocks=baseline_clean,
        rows=rows,
        detected=sum(r["actual_detection"] for r in rows),
        total=len(rows),
        clean_controls=5,
        false_blocks=sum(controls),
        ruleset=RULESET,
    )


SOURCE_FIELDS = [
    k for k in FIELDS if k not in ["variant", "market", "language", "packaging"]
]


def assess_impact(device_id, changed_fields, labels):
    """Only explicit same-device source-field edges propagate a source change."""
    return sorted(
        label["id"]
        for label in labels
        if label["device_id"] == device_id
        and set(changed_fields).intersection(
            label.get("dependency_fields", SOURCE_FIELDS)
        )
    )


def impact_experiment():
    labels = [
        dict(
            id="cardiac-unit", device_id="cardiac", dependency_fields=["warning", "ifu"]
        ),
        dict(id="cardiac-carton", device_id="cardiac", dependency_fields=["warning"]),
        dict(id="monitor-unit", device_id="monitor", dependency_fields=["warning"]),
    ]
    fixtures = [
        ("cardiac", ["warning"], ["cardiac-carton", "cardiac-unit"]),
        ("cardiac", ["ifu"], ["cardiac-unit"]),
        ("monitor", ["warning"], ["monitor-unit"]),
        ("cardiac", ["packaging"], []),
        ("absent", ["warning"], []),
    ]
    results = [
        dict(device_id=d, fields=f, expected=e, observed=assess_impact(d, f, labels))
        for d, f, e in fixtures
    ]
    tp = sum(len(set(r["expected"]) & set(r["observed"])) for r in results)
    fn = sum(len(set(r["expected"]) - set(r["observed"])) for r in results)
    fp = sum(len(set(r["observed"]) - set(r["expected"])) for r in results)
    return dict(
        cases=results,
        true_positive=tp,
        false_negative=fn,
        false_positive=fp,
        recall=tp / (tp + fn) if tp + fn else None,
    )


def targeted_scenarios(changed_fields):
    changed = set(changed_fields)
    return [s for s in SCENARIOS if s[1] in changed or s[1].startswith("_")]
