import type { ProductionOeeAppointmentDetailData } from "../types/production";
import { formatAppointmentDateTime, formatDisplayDate } from "./dates";
import {
  exportDocumentExcel,
  exportDocumentPdf,
  sanitizeFilename,
  type ExportDocument,
} from "./exportDocument";
import { formatDecimal, formatHours, formatPercent, formatProductionQuantity } from "./format";
import { formatOeeAppointmentStatusLabel } from "./oeeAppointmentStatus";

function formatRealHoursSource(source?: string | null): string {
  if (source === "interval") return "Início/fim do apontamento";
  if (source === "h6_tempo") return "H6_TEMPO (fallback)";
  return "—";
}

export function buildAppointmentDetailExportDocument(
  data: ProductionOeeAppointmentDetailData
): ExportDocument {
  const { appointment, time_analysis: timeAnalysis, routing_operations: routing } = data;
  const appointmentId = appointment.appointment_id;

  const appointmentRows: [string, string][] = [
    ["Status", formatOeeAppointmentStatusLabel(appointment)],
    ["Tipo produto", appointment.product_type || "—"],
    ["Filial", appointment.branch || "—"],
    ["Apontamento", String(appointment.appointment_id)],
    ["OP", appointment.production_order || "—"],
    ["Nº OP", appointment.order_number || "—"],
    ["Item", appointment.order_item || "—"],
    ["Produto", appointment.product_code || "—"],
    ["Descrição", appointment.product_description || "—"],
    ["Unidade", appointment.unit || "—"],
    ["CT", appointment.work_center || "—"],
    ["Operação", appointment.operation || "—"],
    ["Descrição operação", appointment.operation_description || "—"],
    ["Recurso", appointment.resource_name || appointment.resource_code || "—"],
    ["Operador", appointment.operator_code || "—"],
    ["Roteiro", appointment.route_code || "—"],
    ["Data produção", formatDisplayDate(appointment.production_date)],
    ["Data apontamento", formatDisplayDate(appointment.appointment_date)],
    [
      "Início",
      formatAppointmentDateTime(appointment.start_date, appointment.start_time),
    ],
    ["Fim", formatAppointmentDateTime(appointment.end_date, appointment.end_time)],
    [
      "Qtd. apontada",
      formatProductionQuantity(appointment.produced_qty, appointment.unit),
    ],
    ["Qtd. perdida", formatProductionQuantity(appointment.lost_qty, appointment.unit)],
    [
      "Qtd. OP",
      formatProductionQuantity(appointment.order_planned_qty, appointment.unit),
    ],
    [
      "Produzido OP",
      formatProductionQuantity(appointment.order_produced_qty, appointment.unit),
    ],
    ["Tipo apontamento", appointment.appointment_type || "—"],
    ["Ponto produção", appointment.production_point_type || "—"],
    ["Eficiência (SH6010)", formatPercent(appointment.oee_pct)],
  ];

  const timeRows: [string, string][] = timeAnalysis
    ? [
        ["Setup (h)", formatHours(timeAnalysis.setup_hours)],
        ["Fator padrão", formatDecimal(timeAnalysis.standard_time_factor, 6)],
        [
          "Qtd. OP",
          formatProductionQuantity(timeAnalysis.order_planned_qty, appointment.unit),
        ],
        [
          "Qtd. apontada",
          formatProductionQuantity(timeAnalysis.produced_qty, appointment.unit),
        ],
        ["Tempo previsto", formatHours(timeAnalysis.planned_hours)],
        ["Tempo real", formatHours(timeAnalysis.real_hours)],
        ["Fonte tempo real", formatRealHoursSource(timeAnalysis.real_hours_source)],
        ["Variação (real - previsto)", formatHours(timeAnalysis.time_variance_hours)],
        ["Ganho/perda de tempo", formatHours(timeAnalysis.time_gained_lost_hours)],
        ["Eficiência (tempos)", formatPercent(timeAnalysis.efficiency_from_times_pct)],
        ["OEE registrado", formatPercent(timeAnalysis.oee_pct)],
        ["Fórmula previsto", timeAnalysis.formula_planned],
        ["Fórmula real", timeAnalysis.formula_real],
        ["Fórmula eficiência", timeAnalysis.formula_efficiency],
        ...(timeAnalysis.findings ?? []).map(
          (finding) =>
            [`Alerta: ${finding.message}`, finding.detail ?? ""] as [string, string]
        ),
      ]
    : [];

  const routingRows =
    routing?.map((row) => [
      row.operation_code ?? "",
      row.operation_description ?? "",
      row.work_center ?? "",
      row.resource_code ?? "",
      formatHours(row.setup_hours ?? null),
      formatHours(row.standard_time_hours_piece ?? null, 4),
      row.bom_level != null ? String(row.bom_level) : "",
      row.is_appointment_operation ? "Operação atual" : "",
    ]) ?? [];

  return {
    title: `Apontamento ${appointmentId}`,
    fieldSections: [
      { title: "Apontamento", rows: appointmentRows },
      ...(timeRows.length ? [{ title: "Análise de tempos", rows: timeRows }] : []),
    ],
    tableSections: routingRows.length
      ? [
          {
            title: "Roteiro",
            headers: [
              "Operação",
              "Descrição",
              "CT",
              "Recurso",
              "Setup (h)",
              "Tempo padrão (h/peça)",
              "Nível BOM",
              "Apontamento",
            ],
            rows: routingRows,
          },
        ]
      : undefined,
  };
}

export async function exportAppointmentDetailExcel(
  data: ProductionOeeAppointmentDetailData
): Promise<void> {
  const document = buildAppointmentDetailExportDocument(data);
  await exportDocumentExcel(document, `apontamento-${data.appointment.appointment_id}`);
}

export async function exportAppointmentDetailPdf(
  data: ProductionOeeAppointmentDetailData
): Promise<void> {
  const document = buildAppointmentDetailExportDocument(data);
  await exportDocumentPdf(document, sanitizeFilename(document.title));
}
