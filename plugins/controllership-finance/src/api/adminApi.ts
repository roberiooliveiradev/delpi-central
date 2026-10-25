/** Cliente da BFF — administração P6 do checklist mestre (MANAGE). */
import { cfApiUrl, httpGet, httpPost, httpPut } from "./httpClient";
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
