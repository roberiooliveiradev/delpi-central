import type {
  ClosingRateData,
  CommercialProposal,
  CommercialProposalDetail,
  CommercialProposalHistoryEvent,
  CommercialProduct,
} from "../types/commercial";
import type { CommercialProductStructureEntry } from "../hooks/useCommercialProductStructures";
import type { RolSeriesPoint } from "../hooks/useCommercialRolSeries";

export type TabularExportFormat = "csv" | "xlsx" | "pdf";

export type ExportAction = {
  format: TabularExportFormat;
  label: string;
  title: string;
};

export const TABULAR_EXPORT_ACTIONS: ReadonlyArray<ExportAction> = [
  { format: "csv", label: "CSV", title: "Baixar CSV" },
  { format: "xlsx", label: "Excel", title: "Baixar Excel" },
  { format: "pdf", label: "PDF", title: "Baixar PDF" },
];

export type ExportColumn = { key: string; label: string };

export type TableExportPayload = {
  title: string;
  columns: ExportColumn[];
  rows: Record<string, unknown>[];
};

export type DashboardKpiExportRow = {
  indicador: string;
  valor: string;
  contexto: string;
};

export type DashboardExportContext = {
  documentTitle: string;
  periodLabel: string;
  scopeLabel: string;
  kpiRows: DashboardKpiExportRow[];
  rolPoints: RolSeriesPoint[];
  funnel: ClosingRateData | null;
  proposals: CommercialProposal[];
};

export type DetailExportContext = {
  documentTitle: string;
  periodLabel: string;
  detail: CommercialProposalDetail;
  products: CommercialProduct[];
  history: CommercialProposalHistoryEvent[];
  structureEntries?: CommercialProductStructureEntry[];
};

export type CommercialExportRequest =
  | {
      kind: "table";
      payload: TableExportPayload;
      format: TabularExportFormat;
    }
  | {
      kind: "tables";
      title: string;
      payloads: TableExportPayload[];
      format: "xlsx" | "pdf";
    }
  | {
      kind: "dashboard";
      context: DashboardExportContext;
      format: TabularExportFormat;
    }
  | {
      kind: "detail";
      context: DetailExportContext;
      format: TabularExportFormat;
    };
