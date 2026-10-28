/** Contrato versionado da Home — espelho de
 * `engineering-api/engineering_app/application/models/home.py` (schema 1.0).
 * O MFE consome o envelope canônico; nunca envelopes internos dos owners.
 */

export type SectionStatus =
  | "available"
  | "empty"
  | "unavailable"
  | "forbidden"
  | "not_implemented";

export type HomeStatus = "available" | "partial" | "unavailable";

export type SectionReason =
  | "timeout"
  | "transport_error"
  | "upstream_error"
  | "contract_error"
  | "no_official_source";

export type HomeItem = {
  id: string;
  kind: string;
  title: string;
  status?: string | null;
  status_label?: string | null;
  date?: string | null;
  href?: string | null;
  source: string;
  meta?: Record<string, unknown>;
};

export type HomeSectionSource = {
  system: string;
  endpoint?: string | null;
};

export type HomeSection = {
  status: SectionStatus;
  source?: HomeSectionSource | null;
  items: HomeItem[];
  total?: number | null;
  reason?: SectionReason | null;
  message?: string | null;
};

export type HomeSectionKey =
  | "attention"
  | "tasks"
  | "lmps"
  | "requests"
  | "activity"
  | "collaboration";

export type HomeSections = Record<HomeSectionKey, HomeSection>;

export type HomeResponse = {
  schema_version: string;
  generated_at: string;
  status: HomeStatus;
  sections: HomeSections;
};

export type HomeEnvelope = {
  success: boolean;
  message?: string | null;
  data: HomeResponse;
  meta?: Record<string, unknown>;
};
