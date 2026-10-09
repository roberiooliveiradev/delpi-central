/**
 * Tipos neutros do Document Host (G7) — transport shapes compartilhados por
 * qualquer backend que hospede um documento BPMN canônico. Nenhum tipo aqui
 * conhece endpoint, app ou storage.
 */

export type ApiIssue = {
  rule_id: string;
  rule_source: string;
  stage: string;
  severity: "ERROR" | "WARNING" | "INFO";
  message: string;
  element_id: string | null;
  path: string | null;
};

export type ValidationReport = {
  evaluated_stages: string[];
  not_evaluated_stages: string[];
  issues: ApiIssue[];
};

export type RevisionSummary = {
  revision_number: number;
  artifact_sha256: string;
  origin: "explicit" | "restore";
  source_revision_number?: number | null;
  created_at: string;
  created_by: string;
  created_by_name?: string | null;
  name?: string | null;
  description?: string | null;
};

export type WriteOutcome = {
  document_id: string;
  version: number;
  changed: boolean;
  artifact_sha256: string;
};

export type DocumentMeta = {
  id: string;
  title: string;
  version: number;
  archived_at?: string | null;
  latest_revision_number?: number | null;
};

export type ApiErrorBody = {
  success: false;
  error?: {
    code: string;
    message: string;
    recoverable?: boolean;
    details?: Record<string, unknown>;
  };
  /** formato alternativo (envelope fail do Transformômetro) */
  message?: string;
  meta?: { request_id: string };
};

/** Erro de transporte do document host — status/code/details preservados
 *  para o SaveMachine/autosave classificar (401, CONFLICT, validation block). */
export class BpmnDocumentError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string;
  readonly details: Record<string, unknown>;

  constructor(status: number, body: ApiErrorBody | null, fallback: string) {
    super(
      body?.error?.message ?? body?.message ?? fallback,
    );
    this.status = status;
    this.code = body?.error?.code ?? "INFRASTRUCTURE_FAILURE";
    this.requestId = body?.meta?.request_id ?? "";
    this.details = body?.error?.details ?? {};
  }
}
