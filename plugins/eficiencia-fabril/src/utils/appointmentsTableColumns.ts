import type { AppointmentsSortColumn } from "./appointmentsTableSort";
import { EF_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import { formatEficienciaFabrilAppointmentStatusLabel } from "./appointmentStatus";
import { formatDisplayDate } from "./dates";
import { formatCurrency, formatMetaPerHour, formatPercent, formatProductionQuantity } from "./format";

export type AppointmentTableColumn = {
  key: AppointmentsSortColumn;
  label: string;
  exportHeader: string;
  hint?: string;
};

export const APPOINTMENT_TABLE_COLUMNS: AppointmentTableColumn[] = [
  {
    key: "data_producao",
    label: "Data",
    exportHeader: "Data",
    hint: EF_HELP_TOOLTIPS.table.dataProducao,
  },
  {
    key: "hora_inicio",
    label: "Início",
    exportHeader: "Início",
    hint: EF_HELP_TOOLTIPS.table.horaInicio,
  },
  {
    key: "hora_final",
    label: "Fim",
    exportHeader: "Fim",
    hint: EF_HELP_TOOLTIPS.table.horaFinal,
  },
  {
    key: "qtd_apontada",
    label: "Qtd. apontada",
    exportHeader: "Qtd. apontada",
    hint: EF_HELP_TOOLTIPS.table.qtdApontada,
  },
  {
    key: "meta_por_hora",
    label: "Meta/hora",
    exportHeader: "Meta/hora",
    hint: EF_HELP_TOOLTIPS.table.metaPorHora,
  },
  {
    key: "filial",
    label: "Filial",
    exportHeader: "Filial",
    hint: EF_HELP_TOOLTIPS.table.filial,
  },
  { key: "op", label: "OP", exportHeader: "OP", hint: EF_HELP_TOOLTIPS.table.op },
  {
    key: "produto_acabado",
    label: "PA",
    exportHeader: "PA",
    hint: EF_HELP_TOOLTIPS.table.produtoAcabado,
  },
  {
    key: "descricao_produto",
    label: "Descrição produto",
    exportHeader: "Descrição produto",
    hint: EF_HELP_TOOLTIPS.table.descricaoProduto,
  },
  {
    key: "descricao_operacao",
    label: "Descrição operação",
    exportHeader: "Descrição operação",
    hint: EF_HELP_TOOLTIPS.table.descricaoOperacao,
  },
  {
    key: "centro_trabalho",
    label: "CT",
    exportHeader: "CT",
    hint: EF_HELP_TOOLTIPS.table.centroTrabalho,
  },
  {
    key: "operador",
    label: "Operador",
    exportHeader: "Operador",
    hint: EF_HELP_TOOLTIPS.table.operador,
  },
  {
    key: "eficiencia_percentual",
    label: "Eficiência",
    exportHeader: "Eficiência (%)",
    hint: EF_HELP_TOOLTIPS.table.eficienciaPercentual,
  },
  {
    key: "resultado_mod",
    label: "Resultado MOD",
    exportHeader: "Resultado MOD",
    hint: EF_HELP_TOOLTIPS.table.resultadoMod,
  },
  {
    key: "status",
    label: "Status",
    exportHeader: "Status",
    hint: EF_HELP_TOOLTIPS.table.status,
  },
];

export const APPOINTMENT_COLUMN_VISIBILITY_ITEMS = APPOINTMENT_TABLE_COLUMNS.map((column) => ({
  key: column.key,
  label: column.label,
}));

/** Colunas mínimas se o usuário desmarcar todas. */
export const APPOINTMENT_COLUMN_EMPTY_FALLBACK: AppointmentsSortColumn[] = [
  "data_producao",
  "op",
  "status",
];

export const APPOINTMENT_COLUMN_STORAGE_KEY =
  "eficiencia-fabril:AppointmentsTable:apontamentos:v1";

export function appointmentExportValue(
  item: EficienciaFabrilItem,
  columnKey: AppointmentsSortColumn
): string | number {
  switch (columnKey) {
    case "data_producao":
      return formatDisplayDate(item.data_producao);
    case "hora_inicio":
      return item.hora_inicio ?? "";
    case "hora_final":
      return item.hora_final ?? "";
    case "qtd_apontada":
      return formatProductionQuantity(item.qtd_apontada, item.unidade);
    case "meta_por_hora":
      return formatMetaPerHour(item.meta_por_hora, item.unidade);
    case "filial":
      return item.filial ?? "";
    case "op":
      return item.op ?? "";
    case "produto_acabado":
      return item.produto_acabado ?? "";
    case "descricao_produto":
      return item.descricao_produto?.trim() || item.produto || "";
    case "descricao_operacao":
      return item.descricao_operacao ?? "";
    case "centro_trabalho":
      return item.centro_trabalho ?? "";
    case "operador":
      return item.nome_operador ?? item.login_operador ?? "";
    case "eficiencia_percentual":
      return item.eficiencia_percentual ?? "";
    case "resultado_mod":
      return item.resultado_mod ?? "";
    case "status":
      return formatEficienciaFabrilAppointmentStatusLabel(item);
    default:
      return "";
  }
}

export function appointmentDisplayCell(
  item: EficienciaFabrilItem,
  columnKey: AppointmentsSortColumn
): string | number {
  switch (columnKey) {
    case "data_producao":
      return formatDisplayDate(item.data_producao);
    case "hora_inicio":
      return item.hora_inicio ?? "—";
    case "hora_final":
      return item.hora_final ?? "—";
    case "qtd_apontada":
      return formatProductionQuantity(item.qtd_apontada, item.unidade);
    case "meta_por_hora":
      return formatMetaPerHour(item.meta_por_hora, item.unidade);
    case "filial":
      return item.filial ?? "—";
    case "op":
      return item.op ?? "—";
    case "produto_acabado":
      return item.produto_acabado ?? "—";
    case "descricao_produto":
      return item.descricao_produto?.trim() || item.produto || "—";
    case "descricao_operacao":
      return item.descricao_operacao?.trim() || "—";
    case "centro_trabalho":
      return item.centro_trabalho ?? "—";
    case "operador":
      return item.nome_operador ?? item.login_operador ?? "—";
    case "eficiencia_percentual":
      return formatPercent(item.eficiencia_percentual);
    case "resultado_mod":
      return formatCurrency(item.resultado_mod);
    case "status":
      return formatEficienciaFabrilAppointmentStatusLabel(item);
    default:
      return "—";
  }
}
