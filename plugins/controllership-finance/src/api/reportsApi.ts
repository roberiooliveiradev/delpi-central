/** Cliente da BFF — matriz R01–R15 (superfície honesta, doc 93). */
import { cfApiUrl, httpGet } from "./httpClient";

export type ReportSourceKind =
  | "OPERATIONAL_VIEW"
  | "MANUAL_EVIDENCE"
  | "EXTERNAL"
  | "PENDING_CONTRACT";

export type ReportMatrixEntry = {
  report_id: string;
  label: string;
  source_kind: ReportSourceKind;
  owner: string | null;
  operational_view: string | null;
  note: string;
  checklist_items: number;
  items_validated: number;
  items_terminal: number;
  items_pending: number;
  coverage: "validated" | "partial" | "pending";
};

export type ReportMatrix = {
  period: string;
  reports: ReportMatrixEntry[];
};

type Envelope<T> = { data?: T };

export async function listReportMatrix(
  period: string,
  signal?: AbortSignal,
): Promise<ReportMatrix | null> {
  const envelope = await httpGet<Envelope<ReportMatrix>>(
    cfApiUrl(`/closing/competences/${period}/reports`),
    { signal },
  );
  return envelope?.data ?? null;
}
