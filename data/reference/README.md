# Public device-reference bundle

This small, real, non-patient metadata sample combines **openFDA UDI / AccessGUDID** and **FDA device product classification**. It is separate from the fictional labeling workspace and the synthetic mutation corpus.

- `openfda-device-reference.json`: allowlisted records, explicit category joins, source URLs, public versions, retrieval timestamps and raw-response checksums.
- `openfda-device-reference.csv`: compact spreadsheet export; potentially active spreadsheet prefixes are neutralized.
- Reproduce from the project root with `python -m scripts.fetch_reference_data`. The APIs require no key for this small sample. Results may change when FDA updates its sources.

## Combination method

Search two UDI records for each of infusion, cardiac and monitor descriptions. Join each explicit `product_codes[].code` to `classification.product_code`. A device may have multiple product codes, so category-join rows are not unique devices. Deduplicate by public UDI record key, public version and product code. Missing or ambiguous classification matches remain unresolved; contradictions are reported rather than overwritten. No name-based fuzzy matching is used.

**This does not establish device equivalence, FDA approval, market authorization, approved safety warnings or label correctness.** The import script never writes to the application database. These rows are not training data and are not used as approved label evidence or as ground truth for the mutation benchmark.

## Data rights and exclusions

Data provided by the U.S. Food and Drug Administration: https://open.fda.gov. Reviewed source terms: https://open.fda.gov/license/ and https://open.fda.gov/terms/.

openFDA generally makes its material available under CC0, with explicit third-party exceptions. **GMDN term codes, names and definitions have separate licensing restrictions and are excluded.** Customer/contact records, emails, phone numbers, company names and free-text clinical narratives are also excluded by a field allowlist. No patient records or adverse-event narratives are collected. Product names and identifiers do not imply manufacturer or FDA endorsement. The source data is unvalidated and must not be used to make medical-care decisions.

## Synthetic-data eligibility

Synthetic fixtures are useful for reproducible fault injection and avoiding patient data. They do not automatically satisfy a hackathon's dataset or Meta-model requirements. The official hackathon rules/link have been requested and eligibility remains unverified. Report synthetic and public-reference experiments separately; never relabel synthetic detection rates as real-world clinical validation.
