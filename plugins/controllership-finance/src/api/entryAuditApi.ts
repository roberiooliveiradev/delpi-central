import {
  cfApiUrl,
  httpGet,
  httpGetBlob,
  httpPost,
} from "./httpClient";

type CfEnvelope<T> = {
  success: boolean;
  data: T;
  meta?: { branches_unavailable?: string[] } & Record<string, unknown>;
};

export type EntryAuditStatus =
  | "queued"
  | "running"
  | "done"
  | "partial"
  | "failed";

export type EntryAuditOption = {
  code: string;
  label?: string;
  name?: string;
  species?: string;
  state?: string;
  tax_id?: string;
  default?: boolean;
};

export type EntryAuditOptions = {
  branches: EntryAuditOption[];
  document_types: EntryAuditOption[];
};

export type EntryAuditAnalysisListItem = {
  id: string;
  date_from: string;
  date_to: string;
  document_types: string[];
  branches: string[];
  status: EntryAuditStatus;
  requested_via: "user" | "clara";
  created_at: string;
  finished_at: string | null;
};

export type EntryAuditRun = {
  branch: string;
  status: EntryAuditStatus;
  stage: string;
  documents_read: number | null;
  xml_downloaded: number | null;
  counts: Record<string, number>;
  error: string | null;
};

export type EntryAuditAnalysis = {
  id: string;
  status: EntryAuditStatus;
  date_from: string;
  date_to: string;
  document_types: string[];
  branches: string[];
  runs: EntryAuditRun[];
  counts: Record<string, number>;
  config: Record<string, unknown>;
};

export type EntryAuditPage<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  branches_unavailable?: string[];
};

export type EntryAuditKpis = {
  documents: number;
  occurrences: number;
  high: number;
  pending: number;
  resolved: number;
  xml_unavailable: number;
  gross_checked: number;
  high_difference: number;
};

export type EntryAuditSummary = {
  kpis: EntryAuditKpis;
  previous: EntryAuditKpis;
  conformity: {
    clean: number;
    divergent: number;
    unmatched_open: number;
    unmatched_explained: number;
    posted_outside_period: {
      count: number;
      by_date: Array<{ date: string; count: number }>;
    };
  };
  branches_unavailable?: string[];
};

export type EntryAuditCount = { name: string; count: number };

export type EntryAuditBreakdowns = {
  by_severity: EntryAuditCount[];
  by_theme: EntryAuditCount[];
  suppliers: EntryAuditCount[];
  tes: EntryAuditCount[];
  branches_unavailable?: string[];
};

export type EntryAuditDaily = {
  series: EntryAuditCount[];
  previous: EntryAuditCount[];
  period: [string, string];
  branches_unavailable?: string[];
};

export type EntryAuditLinks = {
  xml: string | null;
  danfe: string | null;
  dacte: string | null;
};

export type EntryAuditOccurrence = {
  stable_key: string;
  rule_id?: string | null;
  rule_name?: string | null;
  severity?: string | null;
  theme?: string | null;
  title?: string | null;
  document_number?: string | null;
  item?: string | null;
  field?: string | null;
  field_label?: string | null;
  protheus_value?: string | number | null;
  xml_value?: string | number | null;
  difference?: string | number | null;
  series?: string | null;
  supplier_name?: string | null;
  tes?: string | null;
  why?: string | null;
  action?: string | null;
  access_key?: string | null;
  status: "pending" | "resolved";
  history?: Array<{ event: string; at: string | null; actor: string }>;
  links?: EntryAuditLinks;
  clara_suggestion?: string | null;
};

export type EntryAuditDocument = Record<string, unknown> & {
  stable_key?: string;
  branch?: string;
  document_number?: string;
  supplier_name?: string;
  document_type?: string;
  situation?: string;
  access_key?: string;
  comparison?: Record<string, unknown>;
  links?: EntryAuditLinks;
};

export type EntryAuditTes = Record<string, unknown> & {
  branch?: string;
  code?: string;
  tes?: string;
  description?: string;
};

export type EntryAuditFilters = Partial<{
  branch: string;
  severity: string;
  theme: string;
  supplier: string;
  tes: string;
  document_type: string;
  day: string;
  status: string;
  situation: string;
  q: string;
}>;

export type CreateEntryAuditAnalysis = {
  date_from: string;
  date_to: string;
  document_types: string[];
  branches: string[];
  via?: "user";
};

export type EntryAuditCreated = {
  id: string;
  status: EntryAuditStatus;
  created: boolean;
};

export const ENTRY_AUDIT_SEVERITY_URL: Record<string, string> = {
  high: "Alta",
  depends_on_tes: "Depende da TES",
  medium: "Média",
  low: "Baixa",
  info: "Info",
};

function query(values: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([name, value]) => {
    if (value !== undefined && value !== "") params.set(name, String(value));
  });
  const result = params.toString();
  return result ? `?${result}` : "";
}

function unwrap<T>(envelope: CfEnvelope<T>): T {
  if (
    envelope.meta?.branches_unavailable &&
    envelope.data &&
    typeof envelope.data === "object" &&
    !Array.isArray(envelope.data)
  ) {
    return {
      ...envelope.data,
      branches_unavailable: envelope.meta.branches_unavailable,
    } as T;
  }
  return envelope.data;
}

export function listEntryAuditOptions(signal?: AbortSignal) {
  return httpGet<CfEnvelope<EntryAuditOptions>>(
    cfApiUrl("/entry-audit/analyses/options"),
    { signal },
  ).then(unwrap);
}

export function createEntryAuditAnalysis(body: CreateEntryAuditAnalysis) {
  return httpPost<CfEnvelope<EntryAuditCreated>>(
    cfApiUrl("/entry-audit/analyses"),
    body,
  ).then(unwrap);
}

export function listEntryAuditAnalyses(
  filters: Partial<EntryAuditFilters> & {
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  } = {},
  signal?: AbortSignal,
) {
  return httpGet<CfEnvelope<EntryAuditPage<EntryAuditAnalysisListItem>>>(
    cfApiUrl(`/entry-audit/analyses${query(filters)}`),
    { signal },
  ).then(unwrap);
}

export function getEntryAuditAnalysis(id: string, signal?: AbortSignal) {
  return httpGet<CfEnvelope<EntryAuditAnalysis>>(
    cfApiUrl(`/entry-audit/analyses/${encodeURIComponent(id)}`),
    { signal },
  ).then(unwrap);
}

export function getEntryAuditSummary(
  id: string,
  filters: EntryAuditFilters = {},
  signal?: AbortSignal,
) {
  return httpGet<CfEnvelope<EntryAuditSummary>>(
    cfApiUrl(
      `/entry-audit/analyses/${encodeURIComponent(id)}/summary${query(filters)}`,
    ),
    { signal },
  ).then(unwrap);
}

export function getEntryAuditBreakdowns(
  id: string,
  filters: EntryAuditFilters = {},
  signal?: AbortSignal,
) {
  return httpGet<CfEnvelope<EntryAuditBreakdowns>>(
    cfApiUrl(
      `/entry-audit/analyses/${encodeURIComponent(id)}/breakdowns${query(filters)}`,
    ),
    { signal },
  ).then(unwrap);
}

export function getEntryAuditDaily(
  id: string,
  filters: EntryAuditFilters = {},
  signal?: AbortSignal,
) {
  return httpGet<CfEnvelope<EntryAuditDaily>>(
    cfApiUrl(`/entry-audit/analyses/${encodeURIComponent(id)}/daily${query(filters)}`),
    { signal },
  ).then(unwrap);
}

export function listEntryAuditRows<T>(
  id: string,
  resource: "occurrences" | "documents" | "unmatched" | "cte",
  filters: EntryAuditFilters = {},
  page = 1,
  pageSize = 50,
  signal?: AbortSignal,
) {
  return httpGet<CfEnvelope<EntryAuditPage<T>>>(
    cfApiUrl(
      `/entry-audit/analyses/${encodeURIComponent(id)}/${resource}${query({
        ...filters,
        page,
        page_size: pageSize,
      })}`,
    ),
    { signal },
  ).then(unwrap);
}

export function listEntryAuditTes(
  id: string,
  filters: EntryAuditFilters = {},
  signal?: AbortSignal,
) {
  return httpGet<CfEnvelope<{ items: EntryAuditTes[]; branches_unavailable?: string[] }>>(
    cfApiUrl(`/entry-audit/analyses/${encodeURIComponent(id)}/tes${query(filters)}`),
    { signal },
  ).then(unwrap);
}

export function getEntryAuditOccurrence(
  analysisId: string,
  stableKey: string,
  signal?: AbortSignal,
) {
  return httpGet<CfEnvelope<EntryAuditOccurrence>>(
    cfApiUrl(
      `/entry-audit/analyses/${encodeURIComponent(analysisId)}/occurrences/${encodeURIComponent(stableKey)}`,
    ),
    { signal },
  ).then(unwrap);
}

export function setEntryAuditOccurrenceStatus(
  stableKey: string,
  action: "resolve" | "reopen",
  kind: "occurrences" | "unmatched" = "occurrences",
) {
  return httpPost<CfEnvelope<{ stable_key: string; status: string }>>(
    cfApiUrl(`/entry-audit/${kind}/${encodeURIComponent(stableKey)}/${action}`),
    {},
  ).then(unwrap);
}

export function downloadEntryAuditExport(id: string, signal?: AbortSignal) {
  return httpGetBlob(
    cfApiUrl(`/entry-audit/analyses/${encodeURIComponent(id)}/export`),
    { signal },
  );
}

export function entryAuditDownloadUrl(path: string): string {
  return cfApiUrl(path);
}
