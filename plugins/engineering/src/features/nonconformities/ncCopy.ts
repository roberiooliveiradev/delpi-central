import type { NcStatus } from "./types";

export const NC_STATUS_LABELS: Record<NcStatus, string> = {
  open: "Aberta",
  in_progress: "Em andamento",
  done: "Concluída",
};

export const NC_STATUS_VARIANTS: Record<
  NcStatus,
  "neutral" | "success" | "warning" | "danger"
> = {
  open: "danger",
  in_progress: "warning",
  done: "success",
};

export const NC_FIELD_LABELS: Record<string, string> = {
  status: "Status",
  sale_number: "OV",
  lmp_number: "LMP",
  customer_name: "Cliente",
  occurrence_date: "Data de ocorrência",
  registered_at: "Registrado em",
  launch_date: "Data de lançamento",
  last_revision_date: "Última revisão",
  executed_by: "Executado por",
  released_by: "Liberado por",
  defect_description: "Descrição do problema",
  corrective_actions: "Ações corretivas",
  technical_opinion: "Parecer técnico",
  problem_tags: "Problemas identificados",
  products: "Produtos",
  created_by: "Criado por",
  updated_by: "Atualizado por",
};

export const NC_SORT_OPTIONS = [
  { value: "occurrence_date", label: "Data de ocorrência" },
  { value: "registered_at", label: "Data de registro" },
  { value: "sale_number", label: "OV" },
  { value: "lmp_number", label: "LMP" },
  { value: "customer_name", label: "Cliente" },
  { value: "status", label: "Status" },
  { value: "launch_date", label: "Lançamento" },
  { value: "last_revision_date", label: "Última revisão" },
] as const;

export function formatNcDate(value: string | null | undefined): string {
  if (!value) return "—";
  const text = value.slice(0, 10);
  const [y, m, d] = text.split("-");
  return y && m && d ? `${d}/${m}/${y}` : value;
}

export function formatNcDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return formatNcDate(value);
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

/** Ajuda inline (tooltips) da feature NC — HelpTooltip canônico do kit. */
export const NC_HELP = {
  table:
    "Registros oficiais da Engineering API. Clique no cabeçalho para ordenar; clique na linha para abrir o detalhe.",
  dateStart: "Filtra ocorrências a partir desta data (inclusive).",
  dateEnd: "Filtra ocorrências até esta data (inclusive).",
  occurrenceDate: "Data oficial da ocorrência — obrigatória na edição.",
  context:
    "Situação da OV e estrutura dos produtos vêm dos fatos oficiais TOTVS via Engineering API.",
  history:
    "Auditoria append-only: criação e cada atualização com autor, data e campos alterados.",
  importPanel:
    "A importação substitui todo o acervo — execute o dry-run primeiro e confirme a substituição.",
} as const;
