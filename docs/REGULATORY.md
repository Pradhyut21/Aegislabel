# Bounded regulatory demonstration

This educational research prototype uses fictional devices and synthetic specifications. It is not a validated medical-device labeling system, regulatory advice, a certification or a declaration of production readiness. Its rules demonstrate configured checks only.

| Reference context | Demonstrated behavior | Important boundary |
| --- | --- | --- |
| ISO 20417 information supplied by manufacturers | Controlled product identity, manufacturer, warnings and IFU references | No complete standard mapping. The requested ISO 20417:2026 edition has not been independently verified or licensed in this environment; do not claim conformance to that edition. |
| EU MDR 2017/745, Annex I, chapter III | Source-linked label content and configured market/terminology checks | No classification, conformity assessment, CE authorization or complete Annex I coverage. |
| FDA UDI requirements, 21 CFR parts 801 and 830 | Configured UDI-DI and barcode string matching | Synthetic identifiers; no issuing-agency/GUDID integration, production identifier allocation or comprehensive GS1 verification. |
| 21 CFR Part 11 principles | Role separation, audit records, version-bound human review | No legally compliant electronic signatures, validated identity proofing, immutable retention or system validation package. |

Useful official starting points: [EU MDR](https://eur-lex.europa.eu/eli/reg/2017/745/oj), [FDA UDI](https://www.fda.gov/medical-devices/unique-device-identification-system-udi-system), [21 CFR Part 11](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11), [ISO standards catalogue](https://www.iso.org/standards.html). These links are reference context; they are not machine-readable approved requirements automatically imported by this application.

Regulatory-symbol checks compare controlled tokens to the approved specification. They do not certify use of a graphical ISO symbol. Controlled translations are exact approved strings; no automated translation is treated as authoritative. Regulatory updates enter as explicit, approved source changes, not an asserted live monitoring feed.
