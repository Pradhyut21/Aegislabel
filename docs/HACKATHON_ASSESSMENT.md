# Meta Global AI Developer Hackathon: verified facts and open questions

Checked 2026-11-05 against the [official Meta event page](https://dev.meta.ai/events/global-hackathon), its [Cerebral Valley event page](https://cerebralvalley.ai/e/meta-ai-developer-hackathon), and the linked waiver page. These are public-page observations, not an eligibility determination.

- Published project deadline: **November 4, 2026, 9:00 PM ET = November 5, 02:00 UTC**. The first verified clock reading during this review was 02:57 UTC: already after that deadline. No extension was found on the public page. Confirm any late-submission route with the organizers.
- Participation requires selection; the application window was October 13–25, with up to 20,000 accepted applicants. A public repository alone is not an entry.
- The event emphasizes Meta Model API, Muse Spark, Muse Image, SAM 3.1, Meta open weights, and Muse Code. React's origins or an installed SDK alone do not demonstrate model use.
- The publicly accessible event page says detailed Official Rules will be published before October 26. The linked waiver returned a loading page in this environment. **Detailed submission rules, pre-existing-work policy, synthetic-data policy, video duration and participant eligibility could not be verified.** Check the accepted-participant portal and official rules before submitting.
- No live Meta inference was run here. The demo is explicitly deterministic. Never describe it as a live Muse/Llama demo or claim Meta authored or endorsed this application.

## Genuine current API integration

The [official quickstart](https://dev.meta.ai/docs/quickstart) documents `https://api.meta.ai/v1`, `MODEL_API_KEY`, `muse-spark-1.3`, and OpenAI-compatible Chat Completions. `AI_PROVIDER=meta-model` uses that server-side endpoint. Its requests, response validation, truncated-output rejection and fallback are mock-tested. No account credentials or paid calls were used. Authorized live model use remains necessary if the rules require it.

## Dataset suitability

Synthetic records make deliberate safety faults reproducible without touching real product labels or patient data. This is appropriate for a clearly described engineering demonstration, but **does not establish regulatory accuracy, real-world model performance, or hackathon eligibility**.

The separate public research bundle joins openFDA Device UDI with Device Classification by explicit product code. It is not a clinical dataset, not training data, and never supplies approved warnings or release evidence. GMDN terminology, personal/business contacts and narrative reports are excluded. See [reference dataset documentation](../data/reference/README.md) for provenance, licenses and limitations. Combining datasets does not automatically improve the experiment: these public rows add context, not ground truth for labeling correctness.
