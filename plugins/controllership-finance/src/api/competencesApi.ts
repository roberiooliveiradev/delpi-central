/** Cliente da BFF — Competências e checklist esperado (P2-READ). */
import { cfApiUrl, httpGet, httpPost } from "./httpClient";

export type CompetenceSheet = "ELETRONICO" | "FISICO";
export type CompetenceItemOrigin = "TOTVS" | "EXTERNAL" | "MIXED";
export type CompetenceItemRecipient = "CONTABIL" | "FISCAL";
export type CompetenceItemBranchScope = "MATRIX" | "BRANCH" | "BOTH";
export type CompetenceItemState = "EXPECTED";

export type ClosingCompetence = {
  competence_id: string;
  period: string;
  template_version_id: string;
  template_version?: number;
  status: "OPEN";
  opened_at: string;
  item_count?: number;
};

export type CompetenceChecklistItem = {
  snapshot_item_id: string;
  item_key: string;
  sort_order: number;
  sheet: CompetenceSheet;
  name: string;
  origin_kind: CompetenceItemOrigin;
  recipient_area: CompetenceItemRecipient | null;
  applicability: string;
  branch_scope: CompetenceItemBranchScope;
  totvs_report_ref: string | null;
  state: CompetenceItemState;
};

export type CompetenceChecklistItemDetail = CompetenceChecklistItem & {
  purpose: string | null;
  requirement_notes: string | null;
  source_template_item_id: string;
  source_version_id: string;
};

export type CompetenceItemsQuery = {
  sheet?: CompetenceSheet;
  originKind?: CompetenceItemOrigin;
  recipientArea?: CompetenceItemRecipient;
  branchScope?: CompetenceItemBranchScope;
  state?: CompetenceItemState;
};

type Envelope<T> = { success: boolean; data?: T | null };

function buildQuery(params: Record<string, string | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, value);
  }
  return search.toString();
}

export async function listCompetences(
  options?: { signal?: AbortSignal },
): Promise<ClosingCompetence[]> {
  const envelope = await httpGet<Envelope<{ competences: ClosingCompetence[] }>>(
    cfApiUrl("/closing/competences"),
    options,
  );
  return envelope?.data?.competences ?? [];
}

export async function openCompetence(
  period: string,
  options?: { signal?: AbortSignal },
): Promise<ClosingCompetence> {
  const envelope = await httpPost<Envelope<ClosingCompetence>>(
    cfApiUrl("/closing/competences"),
    { period },
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia ao abrir a competência.");
  }
  return envelope.data;
}

export async function getCompetence(
  period: string,
  options?: { signal?: AbortSignal },
): Promise<ClosingCompetence> {
  const envelope = await httpGet<Envelope<ClosingCompetence>>(
    cfApiUrl(`/closing/competences/${period}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Competência não encontrada.");
  }
  return envelope.data;
}

export async function listCompetenceItems(
  period: string,
  query: CompetenceItemsQuery = {},
  options?: { signal?: AbortSignal },
): Promise<CompetenceChecklistItem[]> {
  const qs = buildQuery({
    sheet: query.sheet,
    origin_kind: query.originKind,
    recipient_area: query.recipientArea,
    branch_scope: query.branchScope,
    state: query.state,
  });
  const envelope = await httpGet<
    Envelope<{ items: CompetenceChecklistItem[] }>
  >(cfApiUrl(`/closing/competences/${period}/items${qs ? `?${qs}` : ""}`), options);
  return envelope?.data?.items ?? [];
}

export async function getCompetenceItem(
  period: string,
  itemKey: string,
  options?: { signal?: AbortSignal },
): Promise<CompetenceChecklistItemDetail> {
  const envelope = await httpGet<Envelope<CompetenceChecklistItemDetail>>(
    cfApiUrl(`/closing/competences/${period}/items/${itemKey}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Item do checklist não encontrado.");
  }
  return envelope.data;
}
