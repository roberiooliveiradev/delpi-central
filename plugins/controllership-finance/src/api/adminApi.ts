/** Cliente da BFF — administração P6 do checklist mestre (MANAGE). */
import {
  cfApiUrl,
  httpDelete,
  httpGet,
  httpPost,
  httpPut,
} from "./httpClient";
import type {
  CompetenceItemBranchScope,
  CompetenceItemOrigin,
  CompetenceItemRecipient,
  CompetenceSheet,
  ItemValidationScope,
} from "./competencesApi";

type Envelope<T> = { data?: T };

export type TemplateVersionStatus =
  | "DRAFT"
  | "REVIEW"
  | "PUBLISHED"
  | "INACTIVE";

export type ChecklistTemplate = {
  template_id: string;
  code: string;
  name: string;
  description: string | null;
  created_at: string;
  published_version: number | null;
  draft_version: number | null;
};

export type ChecklistTemplateVersion = {
  version_id: string;
  template_id: string;
  version: number;
  status: TemplateVersionStatus;
  revision: number;
  effective_from_period: string | null;
  published_by: string | null;
  published_at: string | null;
  inactivated_at: string | null;
  created_at: string;
  item_count: number;
};

export type ChecklistTemplateItem = {
  item_id: string;
  item_key: string;
  sort_order: number | null;
  sheet: CompetenceSheet;
  name: string;
  purpose: string | null;
  origin_kind: CompetenceItemOrigin;
  recipient_area: CompetenceItemRecipient | null;
  applicability: "REQUIRED" | "CONDITIONAL" | "OPTIONAL";
  branch_scope: CompetenceItemBranchScope;
  totvs_report_ref: string | null;
  requirement_notes: string | null;
  validation_scope: ItemValidationScope;
};

export type ChecklistTemplateVersionDetail =
  ChecklistTemplateVersion & {
    items: ChecklistTemplateItem[];
  };

export type DraftItemInput = {
  item_key: string;
  sort_order?: number | null;
  sheet: CompetenceSheet;
  name: string;
  purpose?: string | null;
  origin_kind: CompetenceItemOrigin;
  recipient_area?: CompetenceItemRecipient | null;
  applicability?: "REQUIRED" | "CONDITIONAL" | "OPTIONAL";
  branch_scope?: CompetenceItemBranchScope;
  totvs_report_ref?: string | null;
  requirement_notes?: string | null;
  validation_scope?: ItemValidationScope;
};

export type TemplateAuditEvent = {
  event_id: string;
  entity_id: string;
  competence_id: string | null;
  event_type: string;
  actor_subject: string;
  detail: Record<string, unknown>;
  created_at: string;
  version: number;
};

const BASE = "/admin/checklist-templates";

export async function listChecklistTemplates(
  options?: { signal?: AbortSignal },
): Promise<ChecklistTemplate[]> {
  const envelope = await httpGet<
    Envelope<{ templates: ChecklistTemplate[] }>
  >(cfApiUrl(BASE), options);
  return envelope?.data?.templates ?? [];
}

export async function listTemplateVersions(
  templateId: string,
  options?: { signal?: AbortSignal },
): Promise<ChecklistTemplateVersion[]> {
  const envelope = await httpGet<
    Envelope<{ versions: ChecklistTemplateVersion[] }>
  >(cfApiUrl(`${BASE}/${templateId}/versions`), options);
  return envelope?.data?.versions ?? [];
}

export async function getTemplateVersion(
  templateId: string,
  version: number,
  options?: { signal?: AbortSignal },
): Promise<ChecklistTemplateVersionDetail> {
  const envelope = await httpGet<
    Envelope<ChecklistTemplateVersionDetail>
  >(cfApiUrl(`${BASE}/${templateId}/versions/${version}`), options);
  if (!envelope?.data) {
    throw new Error("Versão do checklist não encontrada.");
  }
  return envelope.data;
}

export function createTemplateDraft(
  templateId: string,
): Promise<ChecklistTemplateVersion> {
  return httpPost<Envelope<ChecklistTemplateVersion>>(
    cfApiUrl(`${BASE}/${templateId}/versions`),
    {},
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export function updateTemplateDraft(
  templateId: string,
  version: number,
  payload: { revision: number; items: DraftItemInput[] },
): Promise<ChecklistTemplateVersionDetail> {
  return httpPut<Envelope<ChecklistTemplateVersionDetail>>(
    cfApiUrl(`${BASE}/${templateId}/versions/${version}`),
    payload,
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export function submitVersionForReview(
  templateId: string,
  version: number,
): Promise<ChecklistTemplateVersion> {
  return httpPost<Envelope<ChecklistTemplateVersion>>(
    cfApiUrl(`${BASE}/${templateId}/versions/${version}/submit-review`),
    {},
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export function returnVersionToDraft(
  templateId: string,
  version: number,
  payload: { reason: string },
): Promise<ChecklistTemplateVersion> {
  return httpPost<Envelope<ChecklistTemplateVersion>>(
    cfApiUrl(`${BASE}/${templateId}/versions/${version}/return-to-draft`),
    payload,
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export function publishTemplateVersion(
  templateId: string,
  version: number,
  payload: { effective_from_period: string },
): Promise<ChecklistTemplateVersion> {
  return httpPost<Envelope<ChecklistTemplateVersion>>(
    cfApiUrl(`${BASE}/${templateId}/versions/${version}/publish`),
    payload,
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export type DiscardedVersion = {
  version_id: string;
  version: number;
  status: "DISCARDED";
};

/** Descarte governado de versão DRAFT — OCC via `expected_revision`. */
export function discardTemplateVersion(
  templateId: string,
  version: number,
  expectedRevision: number,
): Promise<DiscardedVersion> {
  return httpDelete<Envelope<DiscardedVersion>>(
    cfApiUrl(
      `${BASE}/${templateId}/versions/${version}` +
        `?expected_revision=${expectedRevision}`,
    ),
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export function inactivateTemplateVersion(
  templateId: string,
  version: number,
): Promise<ChecklistTemplateVersion> {
  return httpPost<Envelope<ChecklistTemplateVersion>>(
    cfApiUrl(`${BASE}/${templateId}/versions/${version}/inactivate`),
    {},
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export type DocumentRequirementResult = {
  item_key: string;
  published_versions: {
    version_id: string;
    version: number;
    effective_from_period: string;
    item_count: number;
  }[];
  no_changes: boolean;
  replayed: boolean;
  audit_event_ids: string[];
};

export type DocumentRequirementPayload = {
  /** Presente = upsert da exigência; omitido = encerramento a partir de
   * `effective_from`. */
  item?: DraftItemInput;
  effective_from: string;
  effective_until?: string | null;
  /** OCC obrigatório — MAX(version) visto pelo cliente (PO D5). */
  base_version: number;
  allow_empty?: boolean;
};

/** DR-1 — configuração documental transacional e idempotente da BFF. */
export function saveDocumentRequirement(
  templateId: string,
  itemKey: string,
  payload: DocumentRequirementPayload,
  idempotencyKey: string,
): Promise<DocumentRequirementResult> {
  return httpPut<Envelope<DocumentRequirementResult>>(
    cfApiUrl(`${BASE}/${templateId}/documents/${itemKey}/requirement`),
    payload,
    { headers: { "Idempotency-Key": idempotencyKey } },
  ).then((envelope) => {
    if (!envelope?.data) throw new Error("Resposta vazia da operação.");
    return envelope.data;
  });
}

export type VersionDeletionReason = {
  code: string;
  count: number;
  label: string;
  periods?: string[];
};

export type VersionDeletionDiagnosis = {
  outcome: "eligible" | "blocked";
  template_id: string;
  version_id: string;
  version: number;
  status: TemplateVersionStatus;
  revision: number;
  item_count: number;
  reasons: VersionDeletionReason[];
  dependents?: {
    exclusive: VersionDeletionReason[];
  };
};

export type VersionDeletionResult = {
  version_id: string;
  version: number;
  status: string;
  deleted: boolean;
  deleted_at: string;
  audit_reference: string;
  replayed?: boolean;
  dependents?: Record<string, number> | null;
};

/** Diagnóstico de vínculos da exclusão definitiva da versão. */
export async function diagnoseTemplateVersionDeletion(
  templateId: string,
  version: number,
  options?: { signal?: AbortSignal },
): Promise<VersionDeletionDiagnosis> {
  const envelope = await httpGet<Envelope<VersionDeletionDiagnosis>>(
    cfApiUrl(
      `${BASE}/${templateId}/versions/${version}/deletion-eligibility`,
    ),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Diagnóstico de exclusão indisponível.");
  }
  return envelope.data;
}

/** Exclusão definitiva da versão — manifesto selado do diagnóstico. */
export function deleteTemplateVersion(
  templateId: string,
  version: number,
  body: {
    expected_version_id: string;
    expected_revision: number;
    expected_item_count: number;
    reason?: string;
    idempotency_key: string;
  },
): Promise<VersionDeletionResult> {
  return httpPost<Envelope<VersionDeletionResult>>(
    cfApiUrl(`${BASE}/${templateId}/versions/${version}/delete`),
    body,
  ).then((envelope) => {
    if (!envelope?.data?.deleted) {
      throw new Error("A exclusão não foi confirmada pela BFF.");
    }
    return envelope.data;
  });
}

export async function listTemplateEvents(
  templateId: string,
  version?: number,
  options?: { signal?: AbortSignal },
): Promise<TemplateAuditEvent[]> {
  const qs = version !== undefined ? `?version=${version}` : "";
  const envelope = await httpGet<
    Envelope<{ events: TemplateAuditEvent[] }>
  >(cfApiUrl(`${BASE}/${templateId}/events${qs}`), options);
  return envelope?.data?.events ?? [];
}

// -- Checklist vivo (CF-CHECKLIST-LIVE-004) ---------------------------------
// Séries, revisões internas append-only e sincronização automática.
// Backend é a única autoridade: OCC `expected_revision`, idempotência
// e confirmação excepcional são validados na BFF.

export type ChecklistSeries = {
  series_id: string;
  template_id: string;
  series_no: number;
  status: "ACTIVE" | "CLOSED";
  start_reason: string | null;
  started_by: string | null;
  started_at: string;
  closed_by: string | null;
  closed_at: string | null;
  versions?: number;
};

export type StartedSeries = {
  series_id: string;
  series_no: number;
  status: string;
  version_id: string;
  replayed: boolean;
};

export type InitializedCatalog = {
  version_id: string;
  items_created: number;
  fingerprint: string;
  replayed: boolean;
};

export type RevisionChangeOp =
  | "ADD"
  | "UPDATE"
  | "RETIRE"
  | "REORDER"
  | "REACTIVATE";

export type RevisionChangeInput = {
  op: RevisionChangeOp;
  item_key: string;
  payload?: Record<string, unknown> | null;
};

export type ChecklistRevisionChange = {
  change_id: string;
  seq: number;
  op: RevisionChangeOp;
  item_key: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
};

export type ChecklistRevision = {
  revision_id: string;
  version_id: string;
  revision_no: number;
  reason: string;
  fingerprint: string;
  reverts_revision_id: string | null;
  reverted_by_revision_id?: string | null;
  created_by: string;
  created_at: string;
  changes?: ChecklistRevisionChange[];
};

export type AppliedRevision = {
  revision_id: string;
  revision_no: number;
  fingerprint: string;
  sync_event_id: string;
  replayed: boolean;
};

export type RevisionPreviewItem = {
  item_key: string;
  op: RevisionChangeOp;
  valid: boolean;
  detail: string | null;
};

export type RevisionPreview = {
  eligible_competences: number;
  affected_items: RevisionPreviewItem[];
};

export type ChecklistSyncRun = {
  run_id: string;
  event_id: string;
  competence_id: string;
  revision_id: string;
  state: string;
  attempts: number;
  skip_reason: string | null;
  exclusions: Record<string, unknown>[];
  last_error: string | null;
  started_at: string | null;
  finished_at: string | null;
};

export type SyncRetryResult = {
  event_id: string;
  runs_reopened: number;
};

export async function listChecklistSeries(
  templateId: string,
  options?: { signal?: AbortSignal },
): Promise<ChecklistSeries[]> {
  const envelope = await httpGet<
    Envelope<{ series: ChecklistSeries[] }>
  >(cfApiUrl(`${BASE}/${templateId}/series`), options);
  return envelope?.data?.series ?? [];
}

export function startChecklistSequence(
  templateId: string,
  body: {
    reason: string;
    confirmation: string;
    idempotency_key: string;
  },
): Promise<StartedSeries> {
  return httpPost<Envelope<StartedSeries>>(
    cfApiUrl(`${BASE}/${templateId}/series`),
    body,
  ).then((envelope) => {
    if (!envelope?.data?.series_id) {
      throw new Error("A nova sequência não foi confirmada pela BFF.");
    }
    return envelope.data;
  });
}

export function initializeChecklistCatalog(
  templateId: string,
  versionId: string,
  body: {
    reason: string;
    items: Record<string, unknown>[];
    idempotency_key: string;
  },
): Promise<InitializedCatalog> {
  return httpPost<Envelope<InitializedCatalog>>(
    cfApiUrl(`${BASE}/${templateId}/versions/${versionId}/items:initialize`),
    body,
  ).then((envelope) => {
    if (!envelope?.data) {
      throw new Error("A carga inicial não foi confirmada pela BFF.");
    }
    return envelope.data;
  });
}

export async function listVersionRevisions(
  templateId: string,
  versionId: string,
  options?: { signal?: AbortSignal },
): Promise<ChecklistRevision[]> {
  const envelope = await httpGet<
    Envelope<{ revisions: ChecklistRevision[] }>
  >(cfApiUrl(`${BASE}/${templateId}/versions/${versionId}/revisions`), options);
  return envelope?.data?.revisions ?? [];
}

export function applyChecklistRevision(
  templateId: string,
  versionId: string,
  body: {
    reason: string;
    expected_revision: number;
    changes: RevisionChangeInput[];
    idempotency_key: string;
  },
): Promise<AppliedRevision> {
  return httpPost<Envelope<AppliedRevision>>(
    cfApiUrl(`${BASE}/${templateId}/versions/${versionId}/revisions`),
    body,
  ).then((envelope) => {
    if (!envelope?.data?.revision_id) {
      throw new Error("A revisão não foi confirmada pela BFF.");
    }
    return envelope.data;
  });
}

export function revertChecklistRevision(
  templateId: string,
  versionId: string,
  revisionId: string,
  body: {
    reason: string;
    expected_revision: number;
    idempotency_key: string;
  },
): Promise<AppliedRevision> {
  return httpPost<Envelope<AppliedRevision>>(
    cfApiUrl(
      `${BASE}/${templateId}/versions/${versionId}` +
        `/revisions/${revisionId}/revert`,
    ),
    body,
  ).then((envelope) => {
    if (!envelope?.data?.revision_id) {
      throw new Error("A reversão não foi confirmada pela BFF.");
    }
    return envelope.data;
  });
}

export function previewChecklistRevision(
  templateId: string,
  versionId: string,
  changes: RevisionChangeInput[],
): Promise<RevisionPreview> {
  return httpPost<Envelope<RevisionPreview>>(
    cfApiUrl(`${BASE}/${templateId}/versions/${versionId}/impact-preview`),
    { changes },
  ).then((envelope) => {
    if (!envelope?.data) {
      throw new Error("Prévia de impacto indisponível.");
    }
    return envelope.data;
  });
}

export async function listChecklistSyncRuns(
  templateId: string,
  revisionId?: string,
  options?: { signal?: AbortSignal },
): Promise<ChecklistSyncRun[]> {
  const qs = revisionId ? `?revision_id=${revisionId}` : "";
  const envelope = await httpGet<
    Envelope<{ runs: ChecklistSyncRun[] }>
  >(cfApiUrl(`${BASE}/${templateId}/sync-runs${qs}`), options);
  return envelope?.data?.runs ?? [];
}

export function retryChecklistSyncEvent(
  templateId: string,
  eventId: string,
): Promise<SyncRetryResult> {
  return httpPost<Envelope<SyncRetryResult>>(
    cfApiUrl(`${BASE}/${templateId}/sync-events/${eventId}:retry`),
    {},
  ).then((envelope) => {
    if (!envelope?.data) {
      throw new Error("O reprocessamento não foi confirmado pela BFF.");
    }
    return envelope.data;
  });
}
