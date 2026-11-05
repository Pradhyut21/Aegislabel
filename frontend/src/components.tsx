import React, { useEffect, useRef } from "react";
import { X, FileText } from "lucide-react";
import type { Finding } from "./types";
export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return (
    <span className={"badge " + tone}>
      <span className="status-dot" />
      {children}
    </span>
  );
}
export function Button({
  children,
  onClick,
  secondary = false,
  disabled = false,
}: {
  children: React.ReactNode;
  onClick: () => void;
  secondary?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      disabled={disabled}
      className={"button " + (secondary ? "secondary" : "primary")}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const opener = document.activeElement as HTMLElement;
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
      opener?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      aria-label={title}
    >
      <div className="dialog-heading">
        <h2>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function FindingCard({ finding: f }: { finding: Finding }) {
  return (
    <div className="finding-card">
      <span className="eyebrow">{f.rule_id}</span>
      <h3>{f.reason_code.replaceAll("_", " ")}</h3>
      <label>
        Expected<span>{String(f.expected)}</span>
      </label>
      <label>
        Observed
        <span className="observed">{String(f.observed) || "(missing)"}</span>
      </label>
      <small>
        <FileText size={12} />
        {f.source_reference}
      </small>
    </div>
  );
}
export function Artwork({ id, name }: { id: string; name: string }) {
  return (
    <div className="artwork-canvas">
      <img
        className="actual-artwork"
        alt={name}
        src={"/api/v1/drafts/" + id + "/artwork.svg"}
      />
    </div>
  );
}
