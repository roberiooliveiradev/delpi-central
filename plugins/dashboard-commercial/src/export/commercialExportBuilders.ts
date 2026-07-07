import type { DataTableColumn } from "../components/dataTableUi";
import type {
  ClosingRateData,
  CommercialProposal,
  CommercialProposalDetail,
  CommercialProposalHistoryEvent,
  CommercialProduct,
} from "../types/commercial";
import type { RolSeriesPoint } from "../hooks/useCommercialRolSeries";
import { COMMERCIAL_ROL_SERIES_LABELS } from "../constants/commercialIndicators";
import { formatDisplayDate } from "../utils/dates";
import { formatCurrency, formatInteger, formatPercent } from "../utils/format";
import {
  formatHistoryDateTime,
  formatProcessStageLabel,
  isHistoryEngineeringFlow,
  resolveHistoryDuration,
  resolveHistoryFlowLabels,
  resolveHistoryStatus,
} from "../utils/proposalHistoryFormatting";
import { parseProductTitle } from "../utils/commercialProductsPresentation";
import type {
  DashboardExportContext,
  DashboardKpiExportRow,
  DetailExportContext,
  TableExportPayload,
} from "../export/types";
import { buildProductStructuresPayload } from "./productStructureExport";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";

const PRODUCT_TYPE_LABELS: Record<string, string> = {
  PA: "Acabado",
  PI: "Intermediário",
  MP: "Matéria-prima",
  ME: "Mercadoria",
  BN: "Beneficiamento",
  AI: "Ativo imobilizado",
};

function formatProductType(type?: string | null): string {
  const normalized = type?.trim().toUpperCase();
  if (!normalized) return "—";
  return PRODUCT_TYPE_LABELS[normalized] ?? normalized;
}

function resolveCellText<T>(row: T, column: DataTableColumn<T>): string {
  if (column.sortValue) {
    const value = column.sortValue(row);
    return value == null ? "—" : String(value);
  }

  const rendered = column.render(row);
  if (rendered == null || rendered === false) return "—";
  if (typeof rendered === "string" || typeof rendered === "number") {
    return String(rendered);
  }

  return "—";
}

export function buildTableExportPayloadFromColumns<T>(
  title: string,
  columns: DataTableColumn<T>[],
  rows: T[],
): TableExportPayload {
  return {
    title,
    columns: columns.map((column) => ({
      key: column.key,
      label: column.header,
    })),
    rows: rows.map((row) =>
      Object.fromEntries(
        columns.map((column) => [column.key, resolveCellText(row, column)]),
      ),
    ),
  };
}

export function buildDashboardKpisPayload(
  rows: DashboardKpiExportRow[],
): TableExportPayload {
  return {
    title: "Indicadores",
    columns: [
      { key: "indicador", label: "Indicador" },
      { key: "valor", label: "Valor" },
      { key: "contexto", label: "Contexto" },
    ],
    rows,
  };
}

export function buildRolSeriesPayload(points: RolSeriesPoint[]): TableExportPayload {
  return {
    title: "Evolução ROL",
    columns: [
      { key: "periodo", label: "Período" },
      { key: "rolMatrix", label: COMMERCIAL_ROL_SERIES_LABELS.filial01 },
      { key: "rolBranch", label: COMMERCIAL_ROL_SERIES_LABELS.filial02 },
    ],
    rows: points.map((point) => ({
      periodo: point.periodo,
      rolMatrix: formatCurrency(point.rolMatrix),
      rolBranch: formatCurrency(point.rolBranch),
    })),
  };
}

export function buildFunnelPayload(
  funnel: ClosingRateData | null,
): TableExportPayload {
  return {
    title: "Funil de conversão",
    columns: [
      { key: "metrica", label: "Métrica" },
      { key: "valor", label: "Valor" },
    ],
    rows: [
      {
        metrica: "Propostas no período",
        valor: formatInteger(funnel?.qtd_proposals),
      },
      {
        metrica: "Propostas ganhas",
        valor: formatInteger(funnel?.qtd_won),
      },
      {
        metrica: "Taxa de conversão",
        valor: formatPercent(funnel?.sales_conversion_rate_pct),
      },
    ],
  };
}

export function buildProposalsPayload(
  proposals: CommercialProposal[],
): TableExportPayload {
  return {
    title: "Propostas",
    columns: [
      { key: "branch", label: OPERATIONAL_UNIT_COLUMN_LABEL },
      { key: "proposal_number", label: "Nº proposta" },
      { key: "revision", label: "Rev." },
      { key: "description", label: "Descrição" },
      { key: "proposal_date", label: "Data" },
      { key: "end_date", label: "Fim" },
      { key: "status", label: "Status" },
      { key: "customer_code", label: "Cliente" },
      { key: "customer_store", label: "Loja" },
    ],
    rows: proposals.map((row) => ({
      branch: formatOperationalUnitCode(row.branch),
      proposal_number: row.proposal_number,
      revision: row.revision || "—",
      description: row.description ?? "—",
      proposal_date: formatDisplayDate(row.proposal_date),
      end_date: formatDisplayDate(row.end_date),
      status: row.status_label ?? row.status_code ?? "—",
      customer_code: row.customer_code ?? "—",
      customer_store: row.customer_store ?? "—",
    })),
  };
}

export function buildProductsPayload(
  products: CommercialProduct[],
): TableExportPayload {
  return {
    title: "Produtos",
    columns: [
      { key: "code", label: "Código" },
      { key: "description", label: "Descrição" },
      { key: "group_code", label: "Grupo" },
      { key: "type", label: "Tipo" },
      { key: "qtd_pi", label: "Qtd PI" },
    ],
    rows: products.map((product) => ({
      code: product.code || "—",
      description: parseProductTitle(product.description),
      group_code: product.group_code ?? "—",
      type: formatProductType(product.type),
      qtd_pi: product.qtd_pi ?? 0,
    })),
  };
}

export function buildHistoryPayload(
  history: CommercialProposalHistoryEvent[],
): TableExportPayload {
  return {
    title: "Histórico da OV",
    columns: [
      { key: "revision", label: "Revisão" },
      { key: "process", label: "Processo" },
      { key: "stage", label: "Estágio" },
      { key: "start", label: "Início" },
      { key: "limit", label: "Limite" },
      { key: "end", label: "Encerramento" },
      { key: "duration", label: "Duração" },
      { key: "status", label: "Status" },
      { key: "state", label: "Situação" },
      { key: "flow", label: "Fluxo" },
      { key: "current", label: "Marcação" },
      { key: "engineering", label: "Eng." },
    ],
    rows: history.map((event) => ({
      revision: event.revision || "—",
      process: formatProcessStageLabel(event.process_code, event.process_label),
      stage: formatProcessStageLabel(event.stage_code, event.stage_label),
      start: formatHistoryDateTime(event.start_date, event.start_time),
      limit: formatHistoryDateTime(event.limit_date, event.limit_time),
      end: event.is_open
        ? "Em andamento"
        : formatHistoryDateTime(event.end_date, event.end_time),
      duration: resolveHistoryDuration(event),
      status: resolveHistoryStatus(event),
      state: event.is_open
        ? "Em andamento"
        : event.is_late
          ? "Atrasado"
          : "Concluído",
      flow: resolveHistoryFlowLabels(event).join(" · ") || "—",
      current: event.is_current
        ? event.is_open
          ? "Atual (em andamento)"
          : "Último evento"
        : "—",
      engineering: isHistoryEngineeringFlow(event) ? "Engenharia" : "—",
    })),
  };
}

export function buildDetailSummaryPayload(
  detail: CommercialProposalDetail,
  periodLabel: string,
): TableExportPayload {
  return {
    title: "Resumo da proposta",
    columns: [
      { key: "campo", label: "Campo" },
      { key: "valor", label: "Valor" },
    ],
    rows: [
      { campo: "OV", valor: detail.proposal_number },
      { campo: "Unidade", valor: formatOperationalUnitCode(detail.branch) },
      { campo: "Revisão", valor: detail.revision },
      { campo: "Descrição", valor: detail.description ?? "—" },
      { campo: "Período consulta", valor: periodLabel },
      { campo: "Status", valor: detail.status_label ?? detail.status_code ?? "—" },
      { campo: "Estágio", valor: detail.stage_label ?? detail.stage ?? "—" },
      { campo: "Processo", valor: detail.process_label ?? detail.process_code ?? "—" },
      { campo: "Abertura", valor: formatDisplayDate(detail.proposal_date) },
      { campo: "Fechamento", valor: formatDisplayDate(detail.end_date) },
      { campo: "Cliente", valor: detail.customer_name ?? "—" },
      { campo: "Código cliente", valor: detail.customer_code ?? "—" },
      { campo: "Loja", valor: detail.customer_store ?? "—" },
      { campo: "Vendedor", valor: detail.seller_name ?? "—" },
      { campo: "Código vendedor", valor: detail.seller_code ?? "—" },
    ],
  };
}

export function buildDashboardExportSheets(
  context: DashboardExportContext,
): TableExportPayload[] {
  return [
    buildDashboardKpisPayload(context.kpiRows),
    buildRolSeriesPayload(context.rolPoints),
    buildFunnelPayload(context.funnel),
    buildProposalsPayload(context.proposals),
  ];
}

export function buildDetailExportSheets(
  context: DetailExportContext,
): TableExportPayload[] {
  const sheets: TableExportPayload[] = [
    buildDetailSummaryPayload(context.detail, context.periodLabel),
    buildProductsPayload(context.products),
  ];

  if (context.structureEntries?.length) {
    sheets.push(buildProductStructuresPayload(context.structureEntries));
  }

  sheets.push(buildHistoryPayload(context.history));

  return sheets;
}

export { buildProductStructuresPayload } from "./productStructureExport";
