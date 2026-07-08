/**
 * Tipos de domínio do Dashboard Comercial + contrato tabular canônico.
 */
export type {
  TabularExportFormat,
  ExportAction,
  ExportColumn,
  TableExportPayload,
} from "@delpi/plugin-ui";

export { TABULAR_EXPORT_ACTIONS } from "@delpi/plugin-ui";

import type {
  ClosingRateData,
  CommercialProposal,
  CommercialProposalDetail,
  CommercialProposalHistoryEvent,
  CommercialProduct,
} from "../types/commercial";
import type { CommercialProductStructureEntry } from "../hooks/useCommercialProductStructures";
import type { RolSeriesPoint } from "../hooks/useCommercialRolSeries";
import type { TabularExportFormat, TableExportPayload } from "@delpi/plugin-ui";

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
