import { ChartNoAxesCombined, Play, Info, RefreshCw } from "lucide-react";
import { Badge, Button } from "./components";
import type {
  Benchmark,
  Workspace,
  Finding,
  LabelConfiguration,
} from "./types";
export function Evaluation({
  benchmark: b,
  ws,
  run,
  busy,
}: {
  benchmark?: Benchmark;
  ws: Workspace;
  run: () => void;
  busy: boolean;
}) {
  if (!b)
    return (
      <div className="panel empty-state">
        <ChartNoAxesCombined size={35} />
        <h2>No experiment has executed yet</h2>
        <p>Run the regression corpus to calculate the comparison.</p>
        <Button disabled={busy} onClick={run}>
          <Play size={15} />
          Execute benchmark
        </Button>
      </div>
    );
  const rows = b.rows;
  const fieldFindings: Finding[] = ws.validation
    .flatMap((v) => v.findings)
    .filter((f: Finding) => f.field in (ws.draft[0]?.fields || {}));
  const linked = fieldFindings.filter((f) =>
    f.source_kind === "registry"
      ? ws.label.some(
          (l) =>
            l.id === f.source_record_id &&
            l[f.field as keyof LabelConfiguration] === f.expected,
        )
      : ws.document.some(
          (d) =>
            d.id === f.source_record_id &&
            d.evidence?.[f.field]?.quote === f.expected,
        ),
  );

  const stale = rows.filter((r) => /approval/i.test(r.scenario));
  const methods = [
    ["Artwork-only comparison", "artwork_detected"],
    ["Deterministic content rules", "rules_detected"],
    ["AegisLabel-FX workflow", "actual_detection"],
  ] as const;
  return (
    <>
      <div className="info-banner">
        <Info size={21} />
        <p>
          Same {b.total} synthetic fault cases for each method. Artwork
          comparison uses visible field differences; content rules omit source
          and approval context. This is a bounded engineering comparison, not an
          independent clinical study.
        </p>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Observed method comparison</h2>
            <p>
              Run {b.id.slice(0, 8)} · {new Date(b.created_at).toLocaleString()}
            </p>
          </div>
          <Badge tone="teal">Actual executions</Badge>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>METRIC</th>
                {methods.map((m) => (
                  <th key={m[1]}>{m[0]}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Critical-error recall</td>
                {methods.map((m) => (
                  <td key={m[1]}>
                    <strong>
                      {(
                        (100 * rows.filter((r) => r[m[1]]).length) /
                        rows.length
                      ).toFixed(1)}
                      %
                    </strong>
                    <small>
                      {rows.filter((r) => r[m[1]]).length} / {rows.length}{" "}
                      faults
                    </small>
                  </td>
                ))}
              </tr>
              <tr>
                <td>Stale-approval escape rate</td>
                {methods.map((m) => (
                  <td key={m[1]}>
                    {(
                      (100 * stale.filter((r) => !r[m[1]]).length) /
                      stale.length
                    ).toFixed(1)}
                    %
                    <small>
                      {stale.filter((r) => !r[m[1]]).length} / {stale.length}{" "}
                      approval faults
                    </small>
                  </td>
                ))}
              </tr>
              <tr>
                <td>False-block rate</td>
                <td>
                  {(
                    (100 * b.baseline_false_blocks.artwork) /
                    b.clean_controls
                  ).toFixed(1)}
                  %
                  <small>
                    {b.baseline_false_blocks.artwork} / {b.clean_controls} clean
                    cases
                  </small>
                </td>
                <td>
                  {(
                    (100 * b.baseline_false_blocks.rules) /
                    b.clean_controls
                  ).toFixed(1)}
                  %
                  <small>
                    {b.baseline_false_blocks.rules} / {b.clean_controls} clean
                    cases
                  </small>
                </td>
                <td>
                  {((100 * b.false_blocks) / b.clean_controls).toFixed(1)}%
                  <small>
                    {b.false_blocks} / {b.clean_controls} clean cases
                  </small>
                </td>
              </tr>
              <tr>
                <td>Change-impact recall</td>
                <td>Not applicable</td>
                <td>Not applicable</td>
                <td>
                  {(100 * (b.impact.recall ?? 0)).toFixed(1)}%
                  <small>
                    {b.impact.true_positive} /{" "}
                    {b.impact.true_positive + b.impact.false_negative} expected
                    impacts · {b.impact.false_positive} false impacts
                  </small>
                </td>
              </tr>
              <tr>
                <td>Evidence traceability coverage</td>
                <td>Not measured</td>
                <td>Not measured</td>
                <td>
                  {fieldFindings.length
                    ? `${((100 * linked.length) / fieldFindings.length).toFixed(1)}%`
                    : "Awaiting validation"}
                  <small>
                    {linked.length} / {fieldFindings.length} findings resolving
                    to source records
                  </small>
                </td>
              </tr>
              <tr>
                <td>Human review time</td>
                <td>Not measured</td>
                <td>Not measured</td>
                <td>
                  {(() => {
                    const durations = ws.draft.flatMap((d) =>
                      d.submitted_at && d.approval && !d.approval.seed
                        ? [
                            new Date(d.approval.timestamp).getTime() -
                              new Date(d.submitted_at).getTime(),
                          ]
                        : [],
                    );
                    return durations.length
                      ? `${Math.round(durations.reduce((sum, value) => sum + value, 0) / durations.length / 1000)}s mean elapsed`
                      : "Awaiting human review";
                  })()}
                  <small>
                    Submission-to-approval elapsed time, includes idle time
                  </small>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel methodology">
        <h2>How to interpret these results</h2>
        <p>
          All faults have explicit expected detections. The suite runs isolated
          copies through the same validation functions used by the release
          workflow. Content-only and artwork-only baselines deliberately have
          narrower information, so their limitations are visible.
        </p>
        <p>
          A small synthetic corpus cannot establish real-world error rates. Five
          clean controls are not a representative manufacturing population.
          Automated checks do not replace clinical, linguistic or regulatory
          review.
        </p>
        <Button secondary disabled={busy} onClick={run}>
          <RefreshCw size={15} />
          Rerun experiment
        </Button>
      </section>
    </>
  );
}
