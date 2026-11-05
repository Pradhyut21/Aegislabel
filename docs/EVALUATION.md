# Evaluation methodology

Run `python -m scripts.benchmark` or execute the Mutation Lab in the interface. JSON results include actual execution times, expected/actual detection, triggered rules and method decisions. No outcome is hardcoded as detected.

## Corpus and controls

24 synthetic single-fault cases cover identifier corruption, missing identifiers, wrong UDI, corrupted barcode, omitted/regressed/partial warnings, stale IFU, wrong variant/packaging, omitted/unsupported symbols, unsupported claims, missing manufacturer, wrong sterility, market, language and translation, missing name, old source revision, stale artwork/source approval, source contradiction and absent approval.

Every case starts from an isolated corrected synthetic source and artwork. Warning-regression cases use the revised demonstration warning even before the live workspace has changed. This makes the benchmark reproducible but means it is a synthetic fixture experiment, not a claim about all live label content. The five clean controls repeat the valid fixture to detect unexpected blocking; their lack of diversity is a limitation. Tests assert approved source and artwork records are untouched.

## Methods

1. **Artwork-only:** exact comparison of deterministic SVG artwork against a reference. Detects visible differences but cannot determine whether a source or reviewer is stale. This is a simple comparison baseline, not OCR or a commercial artwork-inspection product.
2. **Content rules-only:** the same field checks with a fixed source context and no approval requirement. This deliberately omits workflow metadata. It is not intended to represent every possible rules-only implementation.
3. **AegisLabel-FX:** field checks plus current-source consistency, contradiction handling and approval-hash/source/ruleset binding.

Baselines are nested, not independent algorithms. Report this information advantage when interpreting results. All fault cases are designated critical in this configured corpus; there is no empirical estimate of clinical severity.

## Metrics

- Critical-error recall = detected seeded critical faults / seeded critical faults; report numerator and denominator for each method.
- False-block rate = blocked clean cases / executed clean cases, calculated separately for each method.
- Change-impact recall = correctly identified affected labels / expected affected labels on five independent, explicit dependency fixtures. Also report false impacts. Empty-impact cases exercise precision but do not add to the recall denominator.
- Stale-approval escape rate = undetected approval faults / injected approval faults. Includes absent approval as an approval-control fault.
- Evidence traceability = controlled-field findings whose expected value resolves to the cited document evidence or label registry / all controlled-field findings. Workflow metadata checks are excluded. This tests record linkage, not substantive adequacy of clinical evidence. Inspect source evidence in the UI.
- Human review time = mean elapsed submission-to-human-approval duration in stored records. Includes login and idle time; no comparative labor-saving claim is made. Unmeasured baselines display “Not measured.”

`artifacts/benchmark.json` is the reproducible pure run. UI runs are persisted separately with timestamps. A mutation test is not a substitute for validating real artwork. Corpus success does not establish real-world reliability or regulatory compliance. Include adversarial samples, qualified multilingual review and externally developed datasets before drawing broader conclusions.
