import React, { useState, useEffect } from "react";
import { createRoot } from "react-dom/client";
import {
  ShieldCheck,
  LayoutDashboard,
  Box,
  Files,
  GitBranch,
  PanelsTopLeft,
  ScanLine,
  FlaskConical,
  ClipboardCheck,
  History,
  ChartNoAxesCombined,
  ArrowUpRight,
  ArrowRight,
  Plus,
  Search,
  ChevronRight,
  Check,
  CheckCircle2,
  AlertTriangle,
  LockKeyhole,
  Download,
  Play,
  RefreshCw,
  X,
  LogOut,
  Menu,
  FileText,
  Info,
  Activity,
  CornerDownRight,
  ExternalLink,
} from "lucide-react";
import { api, setCsrf } from "./api";
import {
  empty,
  type Workspace,
  type Detail,
  type Draft,
  type Release,
  type AuditVerification,
  type User,
  type Finding,
  type Fields,
} from "./types";
import "./style.css";
import { Badge, Button, Modal, FindingCard, Artwork } from "./components";
import { Evaluation } from "./Evaluation";
import { Overview } from "./Overview";
const nav = [
  ["overview", "Overview", LayoutDashboard],
  ["devices", "Device registry", Box],
  ["documents", "Document intelligence", Files],
  ["changes", "Change impact", GitBranch],
  ["studio", "Label Studio", PanelsTopLeft],
  ["validation", "Validation center", ScanLine],
  ["mutations", "Mutation Lab", FlaskConical],
  ["approvals", "Review & release", ClipboardCheck],
  ["audit", "Evidence & audit", History],
  ["evaluation", "Evaluation", ChartNoAxesCombined],
] as const;
function App() {
  const [u, setU] = useState<User | null>(null),
    [ws, setWs] = useState<Workspace>(empty),
    [page, setPage] = useState("overview"),
    [notice, setNotice] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [mobile, setMobile] = useState(false);
  const [username, setUsername] = useState("author"),
    [password, setPassword] = useState("Aegis-author-2026!"),
    [search, setSearch] = useState("");
  const [modal, setModal] = useState(""),
    [deviceId, setDeviceId] = useState("device-cardiac"),
    [warning, setWarning] = useState(
      "Do not reuse. Inspect packaging before use.",
    );
  const [selected, setSelected] = useState("artwork-cardiac-unit-1"),
    [edit, setEdit] = useState<Fields | null>(null),
    [activeTab, setActiveTab] = useState("findings"),
    [detail, setDetail] = useState<Detail | null>(null),
    [chain, setChain] = useState<AuditVerification | null>(null);
  const refresh = async () => {
    setWs(await api<Workspace>("/workspace"));
  };
  const perform = async (
    fn: () => Promise<void>,
    message = "Saved successfully",
    reload = true,
  ) => {
    setBusy(true);
    setError("");
    try {
      await fn();
      if (reload) await refresh();
      setNotice(message);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    api<User>("/auth/me")
      .then(async (user) => {
        setU(user);
        setCsrf(user.csrf);
        await refresh();
      })
      .catch(() => {});
  }, []);
  useEffect(() => {
    if (!mobile) return;
    const opener = document.activeElement as HTMLElement;
    const sidebar = document.querySelector<HTMLElement>(".sidebar");
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    sidebar?.querySelector<HTMLElement>("nav button")?.focus();
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setMobile(false);
        return;
      }
      if (event.key === "Tab") {
        const controls = Array.from(
          sidebar?.querySelectorAll<HTMLElement>("button,a[href]") || [],
        );
        const first = controls[0],
          last = controls.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    window.addEventListener("keydown", keyboard);
    return () => {
      window.removeEventListener("keydown", keyboard);
      document.body.style.overflow = oldOverflow;
      opener?.focus();
    };
  }, [mobile]);
  const login = async () => {
    await perform(async () => {
      const user = await api<User>("/auth/login", "POST", {
        username,
        password,
      });
      setU(user);
      setCsrf(user.csrf);
    }, "Signed in to the synthetic workspace");
  };
  const go = (p: string) => {
    setPage(p);
    setMobile(false);
    setDetail(null);
    setSearch("");
    setTimeout(() => {
      document
        .querySelector<HTMLElement>("#main")
        ?.focus({ preventScroll: true });
      window.scrollTo(0, 0);
    }, 0);
  };
  const draft = ws.draft.find((d) => d.id === selected) || ws.draft[0];
  const currentLabel = ws.label.find((l) => l.id === draft?.label_id);
  const source = ws.document.find((d) => d.id === currentLabel?.source_id);
  const baseline = ws.draft.find(
    (d) => d.label_id === draft?.label_id && d.label_revision === 1,
  );
  const validation = ws.validation.find((v) => v.id === draft?.validation);
  const latestBench = ws.benchmark.at(-1);
  const changedFields = draft
    ? Object.keys(draft.fields).filter(
        (k) => draft.fields[k] !== baseline?.fields[k],
      )
    : [];
  const latestDrafts = ws.label
    .map(
      (l) =>
        ws.draft
          .filter((d) => d.label_id === l.id)
          .sort((a, b) => b.label_revision - a.label_revision)[0],
    )
    .filter(Boolean);
  const pending = ws.change.filter((c) => c.status === "pending");
  const approvals = latestDrafts.filter((d) => d.status === "in_review");
  const blocked = latestDrafts.filter(
    (d) =>
      ws.validation.find((v) => v.id === d.validation)?.decision === "BLOCKED",
  );
  const createDraft = async (lid: string) => {
    const r = await api<Draft>("/drafts", "POST", { label_id: lid });
    setSelected(r.id);
    setPage("studio");
  };
  const review = async (action: string) => {
    await api("/drafts/" + draft.id + "/review", "POST", {
      revision: draft.revision,
      action,
      comment:
        action === "approve"
          ? "Reviewed artwork, source evidence and configured findings."
          : "",
    });
  };
  const check = () =>
    perform(async () => {
      await api("/drafts/" + draft.id + "/validate", "POST");
    }, "Validation executed against the current approved source");
  const runBench = () =>
    perform(async () => {
      await api("/benchmarks", "POST");
    }, "24 isolated fault scenarios executed");
  const openDraft = (d: Draft) => {
    setSelected(d.id);
    go("studio");
  };
  const matches = (x: unknown) =>
    String(JSON.stringify(x)).toLowerCase().includes(search.toLowerCase());
  if (!u)
    return (
      <div className="login-shell">
        <div className="login-brand">
          <ShieldCheck size={40} />
          <h1>
            AegisLabel<span>-FX</span>
          </h1>
          <p>Change-safe labeling. Evidence at every step.</p>
          <div className="principle">
            AI proposes. Rules decide. Humans approve.
          </div>
          <div className="login-chain">
            <Files />
            <ArrowRight />
            <PanelsTopLeft />
            <ArrowRight />
            <ShieldCheck />
          </div>
          <small>EDUCATIONAL RESEARCH PROTOTYPE · SYNTHETIC DATA</small>
        </div>
        <form
          className="login-card"
          onSubmit={(e) => {
            e.preventDefault();
            void login();
          }}
        >
          <span className="eyebrow">YOUR ASSURANCE WORKSPACE</span>
          <h2>Welcome back.</h2>
          <p>Sign in to manage controlled label revisions.</p>
          <label>
            Username
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <button disabled={busy} className="button primary">
            Sign in <ArrowRight size={16} />
          </button>
          <div className="demo-accounts">
            <strong>Local demonstration accounts</strong>
            <p>
              Author: <code>author / Aegis-author-2026!</code>
              <br />
              Reviewer: <code>reviewer / Aegis-reviewer-2026!</code>
            </p>
            <p>
              Separate accounts keep final approval with an independent human
              reviewer.
            </p>
          </div>
        </form>
      </div>
    );
  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <div className="shell">
        {mobile && (
          <button
            aria-label="Close navigation"
            className="backdrop"
            onClick={() => setMobile(false)}
          />
        )}
        <aside className={mobile ? "sidebar open" : "sidebar"}>
          <a
            className="brand"
            href="/"
            onClick={(e) => {
              e.preventDefault();
              go("overview");
            }}
          >
            <div className="brand-mark">
              <ShieldCheck size={23} />
            </div>
            <span>
              AegisLabel<span className="brand-fx">-FX</span>
              <small>LABEL ASSURANCE PLATFORM</small>
            </span>
          </a>
          <div className="workspace">
            <div className="workspace-icon">A</div>
            <div>
              <strong>Research workspace</strong>
              <span>Synthetic device portfolio</span>
            </div>
            <LockKeyhole size={13} />
          </div>
          <div className="nav-caption">WORKSPACE</div>
          <nav aria-label="Main navigation">
            {nav.map(([id, title, Icon], i) => (
              <React.Fragment key={id}>
                {i === 6 && (
                  <div className="nav-caption assurance">
                    ASSURANCE & GOVERNANCE
                  </div>
                )}
                <button
                  aria-label={title}
                  aria-current={page === id ? "page" : undefined}
                  className={"nav-item " + (page === id ? "active" : "")}
                  onClick={() => go(id)}
                >
                  <Icon size={18} />
                  <span>{title}</span>
                  {id === "changes" && pending.length > 0 && (
                    <span className="nav-count">{pending.length}</span>
                  )}
                  {id === "mutations" && <span className="lab-tag">FX</span>}
                </button>
              </React.Fragment>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="safety-note">
              <ShieldCheck size={18} />
              <strong>Human oversight, always.</strong>
              <p>
                AI proposes. Rules decide.
                <br />
                Humans approve.
              </p>
            </div>
            <div className="profile">
              <div className="avatar">{u.username[0].toUpperCase()}</div>
              <div>
                <strong>
                  {u.username === "author"
                    ? "Label author"
                    : "Quality reviewer"}
                </strong>
                <span>{u.role} · local account</span>
              </div>
              <button
                className="icon-button"
                aria-label="Sign out"
                onClick={() =>
                  void perform(
                    async () => {
                      await api("/auth/logout", "POST");
                      setU(null);
                      setCsrf("");
                    },
                    "Signed out",
                    false,
                  )
                }
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </aside>
        <div className="main-shell" inert={mobile}>
          <header className="topbar">
            <div className="crumb">
              <button
                className="icon-button mobile-menu"
                aria-label="Open navigation"
                onClick={() => setMobile(true)}
              >
                <Menu size={20} />
              </button>
              <span>Workspace</span>
              <ChevronRight size={13} />
              <strong>{nav.find((n) => n[0] === page)?.[1]}</strong>
            </div>
            <div className="top-right">
              <span className="environment">
                <i />
                Local research environment
              </span>
              <span className="header-divider" />
              <button
                className="icon-button"
                aria-label="About this prototype"
                onClick={() => setModal("about")}
              >
                <Info size={18} />
              </button>
              <div className="avatar small">{u.username[0].toUpperCase()}</div>
            </div>
          </header>
          <main id="main" tabIndex={-1}>
            <div className="page-heading">
              <div>
                <div className="eyebrow">
                  {page === "overview"
                    ? "CONTROLLED LABELING OPERATIONS"
                    : page === "mutations"
                      ? "TEST THE CONTROLS. MEASURE THE GAPS."
                      : "AEGISLABEL-FX / " +
                        nav.find((n) => n[0] === page)?.[1].toUpperCase()}
                </div>
                <h1>
                  {page === "overview"
                    ? "Every change. Accounted for."
                    : nav.find((n) => n[0] === page)?.[1]}
                </h1>
                <p>
                  {
                    (
                      {
                        overview:
                          "Your device labels, source changes and release readiness — connected in one workspace.",
                        devices:
                          "A controlled portfolio of fictional medical devices and their labeling variants.",
                        documents:
                          "Versioned source records with field-level, inspectable evidence.",
                        changes:
                          "Follow a source change through every affected label.",
                        studio:
                          "Compare controlled artwork, revise content and inspect the evidence.",
                        validation:
                          "Deterministic checks against approved source requirements.",
                        mutations:
                          "Challenge the validation engine with realistic, isolated labeling faults.",
                        approvals:
                          "Independent human review, bound to the exact artwork version.",
                        audit:
                          "Follow the chain from source evidence to reviewer and artwork hash.",
                        evaluation:
                          "Observed results from the synthetic regression corpus. No invented metrics.",
                      } as Record<string, string>
                    )[page]
                  }
                </p>
              </div>
              <div className="heading-actions">
                {page === "overview" && (
                  <>
                    <Button secondary onClick={() => go("audit")}>
                      <History size={15} />
                      Audit trail
                    </Button>
                    <Button onClick={() => setModal("change")}>
                      <Plus size={16} />
                      New source change
                    </Button>
                  </>
                )}
                {page === "changes" && (
                  <Button onClick={() => setModal("change")}>
                    <Plus size={16} />
                    New source change
                  </Button>
                )}
                {page === "mutations" && (
                  <>
                    <Button disabled={busy} onClick={runBench}>
                      <Play size={15} />
                      Run regression suite
                    </Button>
                    {ws.change.length > 0 && (
                      <Button
                        secondary
                        disabled={busy}
                        onClick={() =>
                          void perform(async () => {
                            await api("/benchmarks", "POST", {
                              change_id: ws.change.at(-1)!.id,
                            });
                          }, "Change-targeted mutations executed")
                        }
                      >
                        Test latest change
                      </Button>
                    )}
                  </>
                )}
                {page === "devices" && (
                  <Badge tone="teal">Synthetic portfolio</Badge>
                )}
              </div>
            </div>
            {busy && (
              <div className="busy" role="status">
                <RefreshCw size={15} />
                Processing controlled operation…
              </div>
            )}
            {error && (
              <div className="notice error" role="alert">
                <AlertTriangle size={17} />
                {error}
                <button aria-label="Dismiss error" onClick={() => setError("")}>
                  <X size={16} />
                </button>
              </div>
            )}
            {notice && !error && (
              <div className="notice" role="status">
                <CheckCircle2 size={17} />
                {notice}
                <button
                  aria-label="Dismiss notification"
                  onClick={() => setNotice("")}
                >
                  <X size={16} />
                </button>
              </div>
            )}
            {page === "overview" && (
              <Overview
                ws={ws}
                pending={pending}
                approvals={approvals}
                latestDrafts={latestDrafts}
                latestBench={latestBench}
                blocked={blocked}
                go={go}
                setModal={setModal}
                setDetail={setDetail}
                setPage={setPage}
                openDraft={openDraft}
              />
            )}
            {page === "devices" && (
              <>
                <div className="filter-bar">
                  <label className="search">
                    <Search size={16} />
                    <input
                      aria-label="Search device registry"
                      placeholder="Search devices, identifiers or markets…"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                  </label>
                  <span>{ws.device.length} synthetic devices</span>
                </div>
                <div className="device-grid">
                  {ws.device.filter(matches).map((d) => (
                    <section className="panel device-card" key={d.id}>
                      <div className="device-card-top">
                        <div className="device-illustration">
                          <Box size={38} strokeWidth={1.2} />
                        </div>
                        <Badge tone="teal">Registered</Badge>
                      </div>
                      <code>{d.identifier}</code>
                      <h2>{d.name}</h2>
                      <p>{d.description}</p>
                      <div className="device-meta">
                        <span>
                          Markets<strong>{d.markets.join(" · ")}</strong>
                        </span>
                        <span>
                          Variants<strong>{d.variants.length}</strong>
                        </span>
                        <span>
                          Labels
                          <strong>
                            {
                              ws.label.filter((l) => l.device_id === d.id)
                                .length
                            }
                          </strong>
                        </span>
                      </div>
                      <div className="card-footer">
                        <Badge>Synthetic record</Badge>
                        <button
                          className="text-link"
                          onClick={() => {
                            setDeviceId(d.id);
                            setModal("change");
                          }}
                        >
                          Assess a change <ArrowRight size={14} />
                        </button>
                      </div>
                    </section>
                  ))}
                </div>
              </>
            )}
            {page === "changes" && (
              <>
                <div className="flow-strip">
                  {[
                    "Source change",
                    "Impact assessment",
                    "Draft revision",
                    "Validation",
                    "Human review",
                    "Release",
                  ].map((s, i) => (
                    <React.Fragment key={s}>
                      <span>
                        <b>{i + 1}</b>
                        {s}
                      </span>
                      {i < 5 && <ChevronRight size={14} />}
                    </React.Fragment>
                  ))}
                </div>
                {!ws.change.length ? (
                  <div className="panel empty-state">
                    <GitBranch size={32} />
                    <h2>No source changes yet</h2>
                    <p>
                      Start the missed-warning demonstration with an approved
                      specification update.
                    </p>
                    <Button onClick={() => setModal("change")}>
                      <Plus size={15} />
                      Create source change
                    </Button>
                  </div>
                ) : (
                  ws.change
                    .filter(matches)
                    .slice()
                    .reverse()
                    .map((c) => (
                      <section className="panel change-card" key={c.id}>
                        <div className="panel-heading">
                          <div>
                            <span className="eyebrow">
                              SPECIFICATION CHANGE · {c.id.slice(0, 8)}
                            </span>
                            <h2>
                              {
                                ws.device.find((d) => d.id === c.device_id)
                                  ?.name
                              }
                            </h2>
                            <p>
                              Approved source R{c.old_version} → R
                              {c.new_version}
                            </p>
                          </div>
                          <Badge
                            tone={c.status === "completed" ? "teal" : "amber"}
                          >
                            {c.status}
                          </Badge>
                        </div>
                        {c.changes.map((x) => (
                          <div key={x.field} className="diff-row">
                            <strong>{x.field}</strong>
                            <del>{String(x.old)}</del>
                            <ArrowRight size={16} />
                            <ins>{String(x.new)}</ins>
                          </div>
                        ))}
                        <div className="impact-heading">
                          <h3>{c.affected_labels.length} affected labels</h3>
                          <span>
                            {ws.label.length - c.affected_labels.length}{" "}
                            unrelated labels unaffected
                          </span>
                        </div>
                        {c.affected_labels.map((id: string) => {
                          const l = ws.label.find((l) => l.id === id);
                          return (
                            <div className="affected-row" key={id}>
                              <CornerDownRight size={17} />
                              <div>
                                <strong>{l?.name}</strong>
                                <small>
                                  {l?.market} · {l?.language.toUpperCase()}
                                </small>
                              </div>
                              <Button
                                disabled={busy}
                                secondary
                                onClick={() =>
                                  void perform(
                                    () => createDraft(id),
                                    "Controlled draft generated from approved source",
                                  )
                                }
                              >
                                <Plus size={14} />
                                Generate draft
                              </Button>
                            </div>
                          );
                        })}
                      </section>
                    ))
                )}
              </>
            )}
            {page === "studio" && draft && (
              <>
                {validation && validation.source_id !== source?.id && (
                  <div className="info-banner">
                    <AlertTriangle size={19} />
                    <p>
                      This validation predates the current approved source.
                      Rerun the checks before review.
                    </p>
                  </div>
                )}
                <div className="studio-toolbar">
                  <label>
                    Artwork revision
                    <select
                      aria-label="Artwork revision"
                      value={draft.id}
                      onChange={(e) => {
                        setSelected(e.target.value);
                        setEdit(null);
                      }}
                    >
                      {ws.draft
                        .slice()
                        .reverse()
                        .map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.fields.identifier} · {d.fields.packaging} · R
                            {d.label_revision} · {d.status}
                          </option>
                        ))}
                    </select>
                  </label>
                  <div className="toolbar-actions">
                    <Badge
                      tone={draft.mode === "deterministic" ? "neutral" : "teal"}
                    >
                      {draft.mode} draft
                    </Badge>
                    {draft.provider_error && (
                      <span className="small-text" title={draft.provider_error}>
                        AI fallback used
                      </span>
                    )}
                    <Button
                      secondary
                      disabled={busy}
                      onClick={() => {
                        setEdit({ ...draft.fields });
                        setModal("edit");
                      }}
                    >
                      Edit artwork
                    </Button>
                    <Button disabled={busy} onClick={check}>
                      <ScanLine size={15} />
                      Run validation
                    </Button>
                  </div>
                </div>
                <div className="studio-grid">
                  <section className="panel artwork-panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">REFERENCE</span>
                        <h2>Previously approved</h2>
                      </div>
                      <Badge tone="teal">R1</Badge>
                    </div>
                    <Artwork
                      id={baseline?.id || draft.id}
                      name="Previously approved artwork"
                    />
                    <div className="artwork-caption">
                      <LockKeyhole size={13} />
                      Preserved approved artwork · synthetic seed
                    </div>
                  </section>
                  <section className="panel artwork-panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">WORKING REVISION</span>
                        <h2>Proposed artwork</h2>
                      </div>
                      <Badge tone="amber">R{draft.label_revision}</Badge>
                    </div>
                    <Artwork id={draft.id} name="Proposed artwork" />
                    <div className="artwork-caption">
                      <Activity size={13} />
                      {changedFields.length} changed fields ·{" "}
                      {draft.status.replace("_", " ")}
                    </div>
                  </section>
                  <section className="panel evidence-panel">
                    <div
                      className="tabs"
                      role="tablist"
                      aria-label="Artwork details"
                    >
                      {["findings", "evidence", "redline"].map((t) => (
                        <button
                          key={t}
                          role="tab"
                          aria-selected={activeTab === t}
                          tabIndex={activeTab === t ? 0 : -1}
                          onKeyDown={(event) => {
                            const keys = ["findings", "evidence", "redline"];
                            const index = keys.indexOf(t);
                            const next =
                              event.key === "ArrowRight"
                                ? keys[(index + 1) % 3]
                                : event.key === "ArrowLeft"
                                  ? keys[(index + 2) % 3]
                                  : event.key === "Home"
                                    ? keys[0]
                                    : event.key === "End"
                                      ? keys[2]
                                      : null;
                            if (next) {
                              event.preventDefault();
                              setActiveTab(next);
                              const controls =
                                event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>(
                                  "[role=tab]",
                                );
                              controls?.[keys.indexOf(next)]?.focus();
                            }
                          }}
                          onClick={() => setActiveTab(t)}
                        >
                          {t}
                        </button>
                      ))}
                    </div>
                    <div className="evidence-content">
                      {activeTab === "findings" && (
                        <>
                          {validation ? (
                            <>
                              <div
                                className={
                                  "decision " +
                                  (validation.decision === "BLOCKED"
                                    ? "blocked"
                                    : "passed")
                                }
                              >
                                {validation.decision === "BLOCKED" ? (
                                  <AlertTriangle size={19} />
                                ) : (
                                  <ShieldCheck size={19} />
                                )}
                                <div>
                                  <strong>{validation.decision}</strong>
                                  {validation.findings.some(
                                    (f: Finding) =>
                                      !f.passed && f.field === "warning",
                                  ) && <span>SAFETY WARNING MISMATCH</span>}
                                </div>
                              </div>
                              <p className="small-text">
                                {
                                  validation.findings.filter(
                                    (f: Finding) => f.passed,
                                  ).length
                                }{" "}
                                / {validation.findings.length} configured checks
                                passed
                              </p>
                              {validation.findings
                                .filter((f: Finding) => !f.passed)
                                .map((f: Finding) => (
                                  <FindingCard key={f.rule_id} finding={f} />
                                ))}
                              {validation.findings.every(
                                (f: Finding) => f.passed,
                              ) && (
                                <div className="success-note">
                                  <CheckCircle2 size={23} />
                                  <h3>Ready for independent review</h3>
                                  <p>
                                    Configured checks passed. Human approval is
                                    still required.
                                  </p>
                                  <Button
                                    secondary
                                    onClick={() => go("approvals")}
                                  >
                                    Open review queue <ArrowRight size={14} />
                                  </Button>
                                </div>
                              )}
                            </>
                          ) : (
                            <div className="empty-state">
                              <ScanLine size={28} />
                              <h3>Validation has not run</h3>
                              <p>
                                Check this revision against the current approved
                                specification.
                              </p>
                              <button className="text-link" onClick={check}>
                                Run validation <ArrowRight size={14} />
                              </button>
                            </div>
                          )}
                        </>
                      )}
                      {activeTab === "evidence" && (
                        <>
                          <Badge tone="teal">
                            Approved source R{source?.source_revision}
                          </Badge>
                          <h3>{source?.title}</h3>
                          {Object.entries(source?.evidence || {}).map(
                            ([k, v]) => (
                              <div className="evidence-item" key={k}>
                                <strong>{k}</strong>
                                <p>{v.quote}</p>
                                <small>
                                  Page {v.page} · R{source?.source_revision}
                                </small>
                              </div>
                            ),
                          )}
                        </>
                      )}
                      {activeTab === "redline" && (
                        <>
                          {changedFields.length ? (
                            changedFields.map((k) => (
                              <div className="redline" key={k}>
                                <strong>{k}</strong>
                                <del>{baseline?.fields[k]}</del>
                                <ins>{draft.fields[k]}</ins>
                              </div>
                            ))
                          ) : (
                            <p>No field changes against the reference.</p>
                          )}
                        </>
                      )}
                    </div>
                  </section>
                </div>
                <div className="studio-footer">
                  <code>
                    Source R{draft.source_version} · artwork revision R
                    {draft.label_revision}
                  </code>
                  <div>
                    <a
                      className="button secondary"
                      href={"/api/v1/drafts/" + draft.id + "/artwork.svg"}
                      download
                    >
                      SVG <Download size={14} />
                    </a>
                    <a
                      className="button secondary"
                      href={"/api/v1/drafts/" + draft.id + "/artwork.pdf"}
                    >
                      PDF <Download size={14} />
                    </a>
                    <Button
                      secondary
                      onClick={() =>
                        void perform(
                          () => createDraft(draft.label_id),
                          "New draft generated from current source",
                        )
                      }
                    >
                      Regenerate from source
                    </Button>
                    <Button
                      disabled={
                        busy ||
                        draft.status !== "draft" ||
                        !validation ||
                        validation.decision !== "PASS FOR REVIEW" ||
                        validation.source_id !== source?.id
                      }
                      onClick={() =>
                        void perform(
                          () => review("submit"),
                          "Submitted for independent human review",
                        )
                      }
                    >
                      Submit for review <ArrowRight size={14} />
                    </Button>
                  </div>
                </div>
                <div className="panel revision-history">
                  <h3>Revision history</h3>
                  {ws.draft
                    .filter((d) => d.label_id === draft.label_id)
                    .slice()
                    .reverse()
                    .map((d) => (
                      <button key={d.id} onClick={() => setSelected(d.id)}>
                        <code>R{d.label_revision}</code>
                        <Badge tone={d.approval ? "teal" : "neutral"}>
                          {d.status}
                        </Badge>
                        <span>{new Date(d.created_at).toLocaleString()}</span>
                        <ChevronRight size={14} />
                      </button>
                    ))}
                </div>
              </>
            )}
            {page === "validation" && (
              <>
                <div className="filter-bar">
                  <p>
                    <strong>{ws.validation.length}</strong> recorded validation
                    runs
                  </p>
                  <Button onClick={() => go("studio")}>
                    <PanelsTopLeft size={15} />
                    Open Label Studio
                  </Button>
                </div>
                {ws.validation.length === 0 ? (
                  <div className="panel empty-state">
                    <ScanLine size={32} />
                    <h2>No validation runs yet</h2>
                    <p>
                      Open artwork in Label Studio and run the configured
                      checks.
                    </p>
                  </div>
                ) : (
                  ws.validation
                    .slice()
                    .reverse()
                    .map((v) => (
                      <section className="panel" key={v.id}>
                        <div className="panel-heading">
                          <div>
                            <h2>Validation · {v.id.slice(0, 8)}</h2>
                            <p>
                              {v.ruleset} ·{" "}
                              {new Date(v.created_at).toLocaleString()}
                            </p>
                          </div>
                          <Badge
                            tone={v.decision === "BLOCKED" ? "red" : "teal"}
                          >
                            {v.decision}
                          </Badge>
                        </div>
                        <div className="table-wrap">
                          <table>
                            <thead>
                              <tr>
                                <th>RULE / REASON</th>
                                <th>EXPECTED</th>
                                <th>OBSERVED</th>
                                <th>SOURCE</th>
                                <th>DECISION</th>
                              </tr>
                            </thead>
                            <tbody>
                              {v.findings.map((f: Finding) => (
                                <tr key={f.rule_id}>
                                  <td>
                                    <strong>{f.rule_id}</strong>
                                    <small>{f.reason_code}</small>
                                  </td>
                                  <td>{String(f.expected)}</td>
                                  <td>{String(f.observed)}</td>
                                  <td>{f.source_reference}</td>
                                  <td>
                                    <Badge tone={f.passed ? "teal" : "red"}>
                                      {f.passed ? "Pass" : "Critical"}
                                    </Badge>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </section>
                    ))
                )}
              </>
            )}
            {page === "mutations" && (
              <>
                <div className="info-banner">
                  <FlaskConical size={23} />
                  <div>
                    <strong>Faults are injected into isolated copies.</strong>
                    <p>
                      Production artwork and approved source records remain
                      intact. These tests assess the controls; actual artwork
                      still requires validation.
                    </p>
                  </div>
                </div>
                <div className="stats-grid mutation-stats">
                  {[
                    [
                      latestBench
                        ? `${latestBench.detected} / ${latestBench.total}`
                        : "—",
                      "Faults detected",
                    ],
                    [
                      latestBench
                        ? `${((100 * latestBench.detected) / latestBench.total).toFixed(1)}%`
                        : "—",
                      "Observed detection rate",
                    ],
                    [
                      latestBench
                        ? latestBench.total - latestBench.detected
                        : "—",
                      "Escaped faults",
                    ],
                    [
                      latestBench ? latestBench.clean_controls : "—",
                      "Clean control cases",
                    ],
                  ].map(([n, t]) => (
                    <div className="stat-card" key={t}>
                      <span>{t}</span>
                      <strong>{n}</strong>
                      <small>
                        {latestBench
                          ? "Latest executed run"
                          : "Awaiting execution"}
                      </small>
                    </div>
                  ))}
                </div>
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Fault-injection matrix</h2>
                      <p>
                        24 scenarios · 5 core families + packaging, symbols,
                        translations and source integrity
                      </p>
                    </div>
                    {latestBench && (
                      <Badge tone="teal">
                        {latestBench.selection || "full-regression"} ·{" "}
                        {new Date(latestBench.created_at).toLocaleTimeString()}
                      </Badge>
                    )}
                  </div>
                  {!latestBench ? (
                    <div className="empty-state">
                      <FlaskConical size={36} />
                      <h2>Put the validation engine to the test.</h2>
                      <p>
                        Results will appear only after the suite has executed.
                      </p>
                      <Button disabled={busy} onClick={runBench}>
                        <Play size={15} />
                        Run regression suite
                      </Button>
                    </div>
                  ) : (
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>SCENARIO / MUTATION</th>
                            <th>EXPECTED</th>
                            <th>ACTUAL</th>
                            <th>RULE TRIGGERED</th>
                            <th>TIME</th>
                          </tr>
                        </thead>
                        <tbody>
                          {latestBench.rows.map((r) => (
                            <tr key={r.scenario}>
                              <td>
                                <strong>{r.scenario}</strong>
                                <small>{r.mutation}</small>
                              </td>
                              <td>Detect</td>
                              <td>
                                <Badge
                                  tone={r.actual_detection ? "teal" : "red"}
                                >
                                  {r.result}
                                </Badge>
                              </td>
                              <td>
                                <code>{r.rules.join(", ") || "None"}</code>
                              </td>
                              <td>{r.execution_ms} ms</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>
              </>
            )}
            {page === "approvals" && (
              <>
                <div className="info-banner">
                  <LockKeyhole size={22} />
                  <div>
                    <strong>Approval belongs to an exact version.</strong>
                    <p>
                      Artwork changes or newer approved sources make earlier
                      approvals ineligible for release. Prototype accounts are
                      not legally compliant electronic signatures.
                    </p>
                  </div>
                </div>
                {latestDrafts.filter((d) => d.author !== "seed").length ===
                  0 && (
                  <div className="panel empty-state">
                    <ClipboardCheck size={32} />
                    <h2>No revisions awaiting review</h2>
                    <p>
                      Generate, validate and submit a draft from Label Studio.
                    </p>
                    <Button onClick={() => go("changes")}>
                      Open change impact <ArrowRight size={15} />
                    </Button>
                  </div>
                )}
                {latestDrafts
                  .filter((d) => d.author !== "seed")
                  .map((d) => (
                    <section key={d.id} className="panel review-card">
                      <div className="panel-heading">
                        <div>
                          <h2>{d.fields.name}</h2>
                          <p>
                            {d.fields.variant} · {d.fields.packaging} · R
                            {d.label_revision} · Source R{d.source_version}
                          </p>
                        </div>
                        <Badge tone={d.approval ? "teal" : "amber"}>
                          {d.status.replace("_", " ")}
                        </Badge>
                      </div>
                      <div className="review-content">
                        <div>
                          <span className="eyebrow">SAFETY WARNING</span>
                          <blockquote>{d.fields.warning}</blockquote>
                          <p>
                            Author: {d.author}{" "}
                            {d.approval &&
                              ` · Reviewer: ${d.approval.reviewer}`}
                          </p>
                          {d.approval && (
                            <code className="hash">
                              SHA-256 {d.approval.hash}
                            </code>
                          )}
                        </div>
                        <div className="review-actions">
                          <Button secondary onClick={() => openDraft(d)}>
                            Inspect artwork <ArrowUpRight size={14} />
                          </Button>
                          {d.status === "in_review" &&
                            u.role === "reviewer" && (
                              <>
                                <Button
                                  disabled={busy}
                                  onClick={() => {
                                    setSelected(d.id);
                                    setDetail(d);
                                    setModal("approve");
                                  }}
                                >
                                  <Check size={15} />
                                  Approve exact version
                                </Button>
                                <Button
                                  secondary
                                  disabled={busy}
                                  onClick={() =>
                                    void perform(async () => {
                                      await api(
                                        "/drafts/" + d.id + "/review",
                                        "POST",
                                        {
                                          revision: d.revision,
                                          action: "reject",
                                          comment:
                                            "Rejected by reviewer; revise and resubmit.",
                                        },
                                      );
                                    }, "Revision rejected")
                                  }
                                >
                                  Reject revision
                                </Button>
                              </>
                            )}
                          {d.status === "in_review" &&
                            u.role !== "reviewer" && (
                              <p className="small-text">
                                Sign in as reviewer to approve.
                              </p>
                            )}
                          {d.status === "approved" && d.approval_current && (
                            <Button
                              disabled={busy}
                              onClick={() =>
                                void perform(async () => {
                                  const r = await api<Release>(
                                    "/drafts/" + d.id + "/release",
                                    "POST",
                                  );
                                  setDetail(r);
                                  setModal("release");
                                }, "Traceable release package generated")
                              }
                            >
                              <Download size={15} />
                              Generate release package
                            </Button>
                          )}
                          {d.approval &&
                            !d.approval_current &&
                            d.status !== "released" && (
                              <Button
                                secondary
                                disabled={busy}
                                onClick={() =>
                                  void perform(
                                    () => createDraft(d.label_id),
                                    "Current-source draft generated; fresh approval required",
                                  )
                                }
                              >
                                Create current-source draft
                              </Button>
                            )}
                          {d.status === "released" &&
                            ws.release
                              .filter((r) => r.draft_id === d.id)
                              .map((r) => (
                                <a
                                  key={r.id}
                                  className="button primary"
                                  href={
                                    "/api/v1/releases/" + r.id + "/download"
                                  }
                                >
                                  <Download size={15} />
                                  Download release ZIP
                                </a>
                              ))}
                        </div>
                      </div>
                    </section>
                  ))}
              </>
            )}
            {page === "documents" && (
              <>
                <div className="upload-panel">
                  <div className="doc-icon">
                    <Files size={25} />
                  </div>
                  <div>
                    <h2>Bring your evidence into the workspace</h2>
                    <p>
                      PDF specifications with controlled “field: value” lines.
                      10 MB / 100 pages maximum. Text-based PDFs only.
                    </p>
                  </div>
                  <Button onClick={() => setModal("upload")}>
                    <Plus size={16} />
                    Upload PDF
                  </Button>
                </div>
                <div className="document-grid">
                  {ws.document
                    .slice()
                    .reverse()
                    .map((d) => (
                      <section className="panel document-card" key={d.id}>
                        <div className="doc-card-heading">
                          <div className="doc-icon">
                            <FileText size={23} />
                          </div>
                          <Badge
                            tone={d.status === "approved" ? "teal" : "amber"}
                          >
                            {d.status}
                          </Badge>
                        </div>
                        <h2>{d.title}</h2>
                        <p>
                          {
                            ws.device.find((x) => x.id === d.device_id)
                              ?.identifier
                          }{" "}
                          ·{" "}
                          {d.source_revision
                            ? "R" + d.source_revision
                            : "Unapproved extraction"}
                        </p>
                        <div className="card-footer">
                          <span className="small-text">
                            {Object.keys(d.fields).length} fields · {d.mode}
                          </span>
                          <button
                            className="text-link"
                            onClick={() => {
                              setDetail(d);
                              setModal("evidence");
                            }}
                          >
                            Inspect evidence <ArrowUpRight size={14} />
                          </button>
                        </div>
                        {d.status === "candidate" && u.role === "reviewer" && (
                          <Button
                            secondary
                            onClick={() =>
                              void perform(async () => {
                                await api(
                                  "/documents/" + d.id + "/approve",
                                  "POST",
                                );
                              }, "Source candidate approved; impact assessed")
                            }
                          >
                            Confirm source fields
                          </Button>
                        )}
                      </section>
                    ))}
                </div>
              </>
            )}
            {page === "audit" && (
              <>
                <div className="filter-bar">
                  <p>Hash-chained audit events · {ws.audit.length} records</p>
                  <Button
                    disabled={busy}
                    secondary
                    onClick={() =>
                      void perform(async () => {
                        setChain(await api<AuditVerification>("/audit/verify"));
                      }, "Audit chain verification completed")
                    }
                  >
                    <ShieldCheck size={15} />
                    Verify chain integrity
                  </Button>
                </div>
                {chain && (
                  <div
                    className={"notice " + (chain.valid ? "" : "error")}
                    role="status"
                  >
                    <ShieldCheck size={18} />
                    {chain.valid
                      ? `Chain verified · ${chain.checked} records`
                      : `Integrity failure at record ${chain.failed_sequence}`}
                  </div>
                )}
                <div className="info-banner">
                  <Info size={21} />
                  <p>
                    Hash chaining detects changes relative to the stored chain.
                    It does not guarantee immutable storage or detect a
                    privileged rewrite or truncated tail without an external
                    anchor.
                  </p>
                </div>
                <section className="panel audit-list">
                  {ws.audit
                    .slice()
                    .reverse()
                    .map((a) => (
                      <button
                        key={a.id}
                        className="audit-row"
                        onClick={() => {
                          setDetail(a);
                          setModal("audit");
                        }}
                      >
                        <div className="audit-number">
                          {String(a.sequence).padStart(2, "0")}
                        </div>
                        <div>
                          <strong>{a.action.replaceAll("_", " ")}</strong>
                          <p>
                            {a.actor} · {new Date(a.timestamp).toLocaleString()}
                          </p>
                          <code>{a.hash.slice(0, 32)}…</code>
                        </div>
                        <ArrowUpRight size={17} />
                      </button>
                    ))}
                </section>
              </>
            )}
            {page === "evaluation" && (
              <Evaluation
                benchmark={latestBench}
                ws={ws}
                run={runBench}
                busy={busy}
              />
            )}
            <footer>
              <span>
                <ShieldCheck size={13} />
                AI proposes. Rules decide. Humans approve.
              </span>
              <span>
                Educational research prototype <i />
                Synthetic data only <i />
                Ruleset FX-2026.1
              </span>
            </footer>
          </main>
        </div>
      </div>
      {modal === "change" && (
        <Modal
          title="Create an approved source change"
          onClose={() => setModal("")}
        >
          <p className="modal-description">
            Update a synthetic specification. The impact engine compares source
            versions and identifies dependent labels.
          </p>
          <label>
            Device
            <select
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
            >
              {ws.device.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Revised safety warning
            <textarea
              maxLength={240}
              rows={3}
              value={warning}
              onChange={(e) => setWarning(e.target.value)}
            />
          </label>
          <div className="info-banner">
            <Info size={18} />
            <p>
              This local demo action simulates receipt of an already approved
              specification. Uploaded extractions require reviewer confirmation.
            </p>
          </div>
          <div className="dialog-actions">
            <Button secondary onClick={() => setModal("")}>
              Cancel
            </Button>
            <Button
              disabled={busy || !warning.trim()}
              onClick={() =>
                void perform(async () => {
                  await api("/changes", "POST", {
                    device_id: deviceId,
                    warning,
                  });
                  setModal("");
                  go("changes");
                }, "Source version created and label impact assessed")
              }
            >
              Detect & assess impact <ArrowRight size={15} />
            </Button>
          </div>
        </Modal>
      )}
      {modal === "edit" && edit && (
        <Modal title="Edit controlled artwork" onClose={() => setModal("")}>
          <p className="modal-description">
            Saving creates a new artwork revision. Prior approvals do not
            transfer. To demonstrate a failure, change the warning back to “Do
            not reuse.”
          </p>
          <div className="edit-grid">
            {Object.entries(edit).map(([k, v]) => (
              <label key={k}>
                {k.replaceAll("_", " ")}
                <input
                  maxLength={240}
                  value={v}
                  onChange={(e) => setEdit({ ...edit, [k]: e.target.value })}
                />
              </label>
            ))}
          </div>
          <div className="dialog-actions">
            <Button secondary onClick={() => setModal("")}>
              Cancel
            </Button>
            <Button
              disabled={busy}
              onClick={() =>
                void perform(async () => {
                  const r = await api<Draft>("/drafts/" + draft.id, "PUT", {
                    revision: draft.revision,
                    fields: edit,
                  });
                  setSelected(r.id);
                  setModal("");
                }, "New artwork revision saved; approval requires fresh review")
              }
            >
              Save new revision
            </Button>
          </div>
        </Modal>
      )}
      {modal === "demo" && (
        <Modal
          title="The missed-warning demonstration"
          onClose={() => setModal("")}
        >
          <p className="modal-description">
            An executable journey using the real source, artwork and validation
            records.
          </p>
          <ol className="demo-steps">
            <li>
              Update the cardiac kit warning to include “Inspect packaging
              before use.”
            </li>
            <li>Generate a draft for an affected label.</li>
            <li>Edit its warning to “Do not reuse.” and run validation.</li>
            <li>Inspect the blocked finding and linked source evidence.</li>
            <li>Regenerate from source, validate and submit for review.</li>
            <li>
              Sign in as reviewer, approve the exact version and generate the
              release ZIP.
            </li>
            <li>
              Run Mutation Lab separately to challenge the warning control.
            </li>
          </ol>
          <Button
            onClick={() => {
              setModal("change");
              setDeviceId("device-cardiac");
            }}
          >
            Start with a source change <ArrowRight size={15} />
          </Button>
        </Modal>
      )}
      {modal === "approve" && detail && "label_revision" in detail && (
        <Modal
          title="Approve exact artwork version"
          onClose={() => setModal("")}
        >
          <p>
            Confirm you have reviewed the artwork and evidence for{" "}
            <strong>R{detail.label_revision}</strong>.
          </p>
          <div className="info-banner">
            <LockKeyhole size={20} />
            <p>
              The server revalidates current source requirements before binding
              your approval. This prototype action is not a legally compliant
              electronic signature.
            </p>
          </div>
          <div className="dialog-actions">
            <Button secondary onClick={() => setModal("")}>
              Cancel
            </Button>
            <Button
              disabled={busy}
              onClick={() =>
                void perform(async () => {
                  await api("/drafts/" + detail.id + "/review", "POST", {
                    revision: detail.revision,
                    action: "approve",
                    comment:
                      "Human reviewed exact artwork version and linked evidence.",
                  });
                  setModal("");
                }, "Approval bound to the exact artwork hash and source version")
              }
            >
              Confirm approval <Check size={15} />
            </Button>
          </div>
        </Modal>
      )}
      {modal === "release" && detail && "summary" in detail && (
        <Modal title="Release package ready" onClose={() => setModal("")}>
          <div className="success-note">
            <ShieldCheck size={35} />
            <h3>Human reviewed. Evidence attached.</h3>
            <p>
              The package contains SVG and PDF artwork, source evidence and a
              release summary.
            </p>
          </div>
          <a
            className="button primary"
            href={"/api/v1/releases/" + detail.id + "/download"}
          >
            <Download size={15} />
            Download release ZIP
          </a>
        </Modal>
      )}
      {modal === "upload" && (
        <Modal title="Upload a specification PDF" onClose={() => setModal("")}>
          <label>
            Device
            <select
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
            >
              {ws.device.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
          <p className="modal-description">
            Use controlled field names such as warning, identifier and ifu
            followed by a colon. The extraction remains a candidate until a
            reviewer confirms all fields.
          </p>
          <label>
            PDF file
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f)
                  void perform(async () => {
                    const form = new FormData();
                    form.append("file", f);
                    await api(
                      "/documents/upload?device_id=" +
                        encodeURIComponent(deviceId),
                      "POST",
                      form,
                    );
                    setModal("");
                  }, "PDF extracted using deterministic field parsing; review evidence before approval");
              }}
            />
          </label>
        </Modal>
      )}
      {["evidence", "audit"].includes(modal) && detail && (
        <Modal
          title={modal === "evidence" ? "Source evidence" : "Audit record"}
          onClose={() => setModal("")}
        >
          {modal === "evidence" && "evidence" in detail ? (
            <>
              <Badge tone="teal">{detail.mode} extraction</Badge>
              <h3>{detail.title}</h3>
              <a
                className="button secondary"
                href={"/api/v1/documents/" + detail.id + "/pdf"}
                target="_blank"
                rel="noreferrer"
              >
                Open source PDF <ExternalLink size={14} />
              </a>
              {detail.contradiction && (
                <div className="notice error">
                  <AlertTriangle size={18} />
                  Conflicting source values. Correct and re-upload before
                  approval.
                </div>
              )}
              {Object.entries(detail.evidence || {}).map(([k, v]) => (
                <div className="evidence-item" key={k}>
                  <strong>{k}</strong>
                  <p>{v.quote}</p>
                  <small>
                    Document {detail.id.slice(0, 12)} · R
                    {detail.source_revision} · Page {v.page}
                  </small>
                </div>
              ))}
            </>
          ) : (
            <pre>{JSON.stringify(detail, null, 2)}</pre>
          )}
        </Modal>
      )}
      {modal === "about" && (
        <Modal title="About AegisLabel-FX" onClose={() => setModal("")}>
          <p>
            A change-aware medical-device labeling research prototype for
            TELIPORT Season 4, Case Study 4.
          </p>
          <div className="info-banner">
            <ShieldCheck size={24} />
            <p>AI proposes. Rules decide. Humans approve.</p>
          </div>
          <p>
            Checks demonstrate a bounded configured ruleset. This application is
            not certified, production validated or a substitute for regulatory
            review. All devices are fictional. No paid AI service is enabled.
          </p>
        </Modal>
      )}
    </>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
