export type Fields = Record<string, string>;
export interface RecordBase {
  id: string;
  revision: number;
}
export interface Device extends RecordBase {
  name: string;
  identifier: string;
  description: string;
  synthetic: boolean;
  markets: string[];
  languages: string[];
  variants: string[];
}
export interface EvidenceLocation {
  page: number | null;
  quote: string;
  bbox: number[] | null;
  locations?: [number, number[]][];
}
export interface SourceDocument extends RecordBase {
  device_id: string;
  title: string;
  source_revision: number;
  status: "approved" | "candidate" | "processed";
  fields: Fields;
  evidence: Record<string, EvidenceLocation>;
  mode: string;
  created_at: string;
  contradiction?: boolean;
  provider_error?: string | null;
  file_hash?: string;
}
export interface LabelConfiguration extends RecordBase {
  device_id: string;
  name: string;
  market: string;
  language: string;
  packaging: string;
  variant: string;
  source_id: string;
  dependency_fields: string[];
}
export interface Approval {
  hash: string;
  source_version: number;
  ruleset: string;
  reviewer: string;
  timestamp: string;
  seed?: boolean;
  comment?: string;
}
export interface Draft extends RecordBase {
  label_id: string;
  device_id: string;
  fields: Fields;
  source_id: string;
  source_version: number;
  label_revision: number;
  status: "draft" | "in_review" | "approved" | "rejected" | "released";
  author: string;
  approval: Approval | null;
  approval_current: boolean;
  mode: string;
  created_at: string;
  validation: string | null;
  parent_id?: string;
  submitted_at?: string;
  provider_error?: string | null;
}
export interface Finding {
  rule_id: string;
  field: string;
  expected: unknown;
  observed: unknown;
  severity: string;
  source_reference: string;
  source_id?: string;
  source_record_id?: string;
  source_kind?: string;
  reason_code: string;
  passed: boolean;
}
export interface Validation extends RecordBase {
  draft_id: string;
  source_id: string;
  created_at: string;
  decision: "BLOCKED" | "ESCALATE" | "PASS FOR REVIEW";
  findings: Finding[];
  ruleset: string;
  artwork_hash: string;
}
export interface FieldChange {
  field: string;
  old: unknown;
  new: unknown;
}
export interface Change extends RecordBase {
  device_id: string;
  old_source_id: string;
  new_source_id: string;
  old_version: number;
  new_version: number;
  changes: FieldChange[];
  affected_labels: string[];
  status: string;
  created_at: string;
}
export interface MutationRow {
  scenario: string;
  mutation: string;
  expected_detection: boolean;
  actual_detection: boolean;
  result: string;
  rules: string[];
  execution_ms: number;
  artwork_detected: boolean;
  rules_detected: boolean;
}
export interface Benchmark extends RecordBase {
  rows: MutationRow[];
  detected: number;
  total: number;
  clean_controls: number;
  false_blocks: number;
  baseline_false_blocks: { artwork: number; rules: number };
  impact: {
    true_positive: number;
    false_negative: number;
    false_positive: number;
    recall: number | null;
  };
  selection: string;
  changed_fields: string[] | null;
  created_at: string;
  ruleset: string;
}
export interface AuditEvent extends RecordBase {
  sequence: number;
  timestamp: string;
  action: string;
  actor: string;
  detail: Record<string, unknown>;
  previous_hash: string;
  hash: string;
}
export interface AuditVerification {
  valid: boolean;
  checked: number;
  head?: string;
  failed_sequence?: number;
}
export interface Release extends RecordBase {
  draft_id: string;
  summary: Record<string, unknown>;
  fields: Fields;
  created_at: string;
}
export type Detail = SourceDocument | Draft | Change | AuditEvent | Release;
export interface Workspace {
  device: Device[];
  document: SourceDocument[];
  label: LabelConfiguration[];
  draft: Draft[];
  change: Change[];
  validation: Validation[];
  benchmark: Benchmark[];
  audit: AuditEvent[];
  release: Release[];
}
export interface User {
  username: string;
  role: "author" | "reviewer";
  csrf: string;
}
export const empty: Workspace = {
  device: [],
  document: [],
  label: [],
  draft: [],
  change: [],
  validation: [],
  benchmark: [],
  audit: [],
  release: [],
};
