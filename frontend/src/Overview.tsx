import {
  GitBranch,
  ArrowUpRight,
  ArrowRight,
  Box,
  PanelsTopLeft,
  ClipboardCheck,
  FileText,
  CheckCircle2,
  ShieldCheck,
  FlaskConical,
} from "lucide-react";
import { Badge } from "./components";
import type { Change, Draft, Benchmark, Workspace } from "./types";
export function Overview({
  ws,
  pending,
  approvals,
  latestDrafts,
  latestBench,
  blocked,
  go,
  setModal,
  setDetail,
  setPage,
  openDraft,
}: {
  ws: Workspace;
  pending: Change[];
  approvals: Draft[];
  latestDrafts: Draft[];
  latestBench?: Benchmark;
  blocked: Draft[];
  go: (p: string) => void;
  setModal: (p: string) => void;
  setDetail: (d: Change) => void;
  setPage: (p: string) => void;
  openDraft: (d: Draft) => void;
}) {
  return (
    <>
      <div className="overview-banner">
        <div className="banner-icon">
          <GitBranch size={24} />
        </div>
        <div>
          <Badge tone="teal">CHANGE-SAFE BY DESIGN</Badge>
          <h2>A source changes. Your assurance follows.</h2>
          <p>
            Detect impact, revise artwork, challenge the checks, and release
            with evidence.
          </p>
        </div>
        <button onClick={() => setModal("demo")} className="banner-button">
          Run the guided demo <ArrowUpRight size={16} />
        </button>
        <div className="banner-pattern" aria-hidden="true">
          <ShieldCheck size={150} strokeWidth={0.6} />
        </div>
      </div>
      <div className="stats-grid">
        {[
          [
            ws.device.length,
            "Registered devices",
            Box,
            "devices",
            "Synthetic records",
          ],
          [
            latestDrafts.filter((d) => d.approval_current).length,
            "Active label versions",
            PanelsTopLeft,
            "studio",
            "Across packaging variants",
          ],
          [
            pending.length,
            "Pending source changes",
            GitBranch,
            "changes",
            "Awaiting implementation",
          ],
          [
            approvals.length,
            "Pending approvals",
            ClipboardCheck,
            "approvals",
            "Independent review required",
          ],
        ].map(([n, title, Icon, p, sub]) => {
          const I = Icon as typeof Box;
          return (
            <button
              className="stat-card"
              key={String(title)}
              onClick={() => go(String(p))}
            >
              <div>
                <span>{String(title)}</span>
                <I size={17} />
              </div>
              <strong>{String(n)}</strong>
              <small>
                {String(sub)}
                <ArrowUpRight size={14} />
              </small>
            </button>
          );
        })}
      </div>
      <div className="overview-columns">
        <section className="panel changes-panel">
          <div className="panel-heading">
            <div>
              <h2>
                Change control queue{" "}
                <span className="count">{pending.length}</span>
              </h2>
              <p>Source updates that need your attention</p>
            </div>
            <button className="text-link" onClick={() => go("changes")}>
              View all <ArrowRight size={14} />
            </button>
          </div>
          {pending.length ? (
            pending.slice(-3).map((c) => (
              <button
                className="queue-row"
                key={c.id}
                onClick={() => {
                  setDetail(c);
                  setPage("changes");
                }}
              >
                <div className="doc-icon">
                  <FileText size={20} />
                </div>
                <div>
                  <strong>
                    {ws.device.find((d) => d.id === c.device_id)?.name}
                  </strong>
                  <p>
                    {c.changes
                      .map((x) => x.field.replaceAll("_", " "))
                      .join(", ")}{" "}
                    updated · R{c.old_version} → R{c.new_version}
                  </p>
                  <small>{c.affected_labels.length} affected labels</small>
                </div>
                <Badge tone="amber">Needs revision</Badge>
              </button>
            ))
          ) : (
            <div className="empty-state">
              <div className="empty-icon">
                <CheckCircle2 size={26} />
              </div>
              <h3>Your source records are in sync</h3>
              <p>Create a warning change to see the impact engine in action.</p>
              <button className="text-link" onClick={() => setModal("change")}>
                Create a source change <ArrowRight size={14} />
              </button>
            </div>
          )}
          <div className="panel-bottom">
            <span>
              <i className="teal-dot" />
              Explicit product-to-label dependencies
            </span>
            <span>{ws.label.length} label variants monitored</span>
          </div>
        </section>
        <section className="panel readiness">
          <div className="panel-heading">
            <div>
              <h2>Release readiness</h2>
              <p>Current state of the latest artwork revisions</p>
            </div>
            <ShieldCheck size={20} />
          </div>
          <div className="readiness-main">
            <span>
              {latestDrafts.filter((d) => d.approval_current).length}
              <small>/ {latestDrafts.length}</small>
            </span>
            <p>labels with human approval</p>
          </div>
          <div className="segmented-bar">
            {latestDrafts.map((d) => (
              <i
                key={d.id}
                className={
                  d.approval_current
                    ? "ready"
                    : d.status === "in_review"
                      ? "review"
                      : "draft"
                }
              />
            ))}
          </div>
          <div className="readiness-row">
            <span>
              <i className="dot teal" />
              Approved / released
            </span>
            <strong>
              {latestDrafts.filter((d) => d.approval_current).length}
            </strong>
          </div>
          <div className="readiness-row">
            <span>
              <i className="dot amber" />
              Draft revisions
            </span>
            <strong>
              {latestDrafts.filter((d) => d.status === "draft").length}
            </strong>
          </div>
          <div className="readiness-row">
            <span>
              <i className="dot red" />
              Blocked validation
            </span>
            <strong>{blocked.length}</strong>
          </div>
          <button className="readiness-link" onClick={() => go("approvals")}>
            Open review workspace <ArrowRight size={15} />
          </button>
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Label portfolio</h2>
            <p>Latest artwork revisions across your device portfolio</p>
          </div>
          <button className="text-link" onClick={() => go("devices")}>
            Device registry <ArrowRight size={14} />
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>DEVICE / LABEL</th>
                <th>MARKET</th>
                <th>PACKAGING</th>
                <th>REVISION</th>
                <th>STATUS</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {latestDrafts.map((d) => (
                <tr key={d.id}>
                  <td>
                    <div className="cell-title">
                      <span className="table-icon">
                        <Box size={17} />
                      </span>
                      <div>
                        <strong>{d.fields.name}</strong>
                        <small>
                          {d.fields.identifier} · {d.fields.variant}
                        </small>
                      </div>
                    </div>
                  </td>
                  <td>
                    {d.fields.market}{" "}
                    <span className="muted">
                      / {d.fields.language.toUpperCase()}
                    </span>
                  </td>
                  <td>{d.fields.packaging}</td>
                  <td>
                    <code>R{d.label_revision}</code>
                  </td>
                  <td>
                    <Badge
                      tone={
                        d.approval_current
                          ? "teal"
                          : d.status === "in_review"
                            ? "amber"
                            : "neutral"
                      }
                    >
                      {d.approval && !d.approval_current
                        ? "Approval stale"
                        : d.status.replace("_", " ")}
                    </Badge>
                  </td>
                  <td>
                    <button
                      className="icon-button"
                      aria-label={
                        "Open " + d.fields.identifier + " " + d.fields.packaging
                      }
                      onClick={() => openDraft(d)}
                    >
                      <ArrowUpRight size={17} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <div className="assurance-strip">
        <FlaskConical size={21} />
        <div>
          <strong>Confidence is tested, not assumed.</strong>
          <p>
            {latestBench
              ? `${latestBench.detected} of ${latestBench.total} injected faults detected in the latest run.`
              : "Run real fault-injection tests against the same controls that validate your labels."}
          </p>
        </div>
        <button className="text-link" onClick={() => go("mutations")}>
          Explore Mutation Lab <ArrowRight size={15} />
        </button>
      </div>
    </>
  );
}
