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

/** Ajuda inline (tooltips) da feature NC — sempre no texto do próprio
 * label via HelpTooltip/FieldLabel canônicos (sem ícone `?` separado). */
export const NC_HELP = {
  table:
    "Registros oficiais da Engineering API. Clique no cabeçalho para ordenar; clique na linha para abrir o detalhe.",
  indicators:
    "Indicadores oficiais calculados pela Engineering API — não são recalculados no Portal.",
  daysWithoutNc:
    "Dias consecutivos desde a data da última não conformidade registrada até hoje.",
  recordDaysWithoutNc:
    "Maior sequência histórica de dias sem não conformidade registrada.",
  filters:
    "Filtros aplicados no servidor sobre o acervo oficial — Filtrar executa a consulta e Limpar restaura tudo.",
  status: "Situação do tratamento: aberta, em andamento ou concluída.",
  saleNumber: "Ordem de venda (OV) vinculada à não conformidade.",
  lmpNumber: "Número da LMP de origem, quando a NC veio de uma lista.",
  customerName: "Cliente associado à ordem de venda registrada.",
  productCode:
    "Código do produto associado — filtra NCs que tenham este produto vinculado.",
  problemTag:
    "Tag compartilhada que classifica o problema — o catálogo é reutilizado entre registros.",
  dateStart: "Filtra ocorrências a partir desta data (inclusive).",
  dateEnd: "Filtra ocorrências até esta data (inclusive).",
  colOccurrence: "Data oficial da ocorrência registrada na NC.",
  colProducts:
    "Produtos vinculados ao registro — a lista completa aparece no detalhe da NC.",
  colDefect: "Resumo da descrição do problema informado no registro.",
  colRegisteredAt: "Data e hora em que o registro foi criado.",
  occurrenceDate: "Data oficial da ocorrência — obrigatória na edição.",
  registeredAt: "Momento em que o registro foi criado na Engineering API.",
  launchDate: "Data de lançamento do item no processo produtivo.",
  lastRevisionDate: "Data da última revisão relacionada à ocorrência.",
  executedBy:
    "Nome livre de quem executou a tratativa — ainda não é um vínculo com usuário do Portal.",
  releasedBy:
    "Nome livre de quem liberou a tratativa — ainda não é um vínculo com usuário do Portal.",
  createdBy: "Usuário do Portal que criou o registro.",
  updatedBy: "Usuário do Portal que fez a última alteração do registro.",
  defectDescription:
    "Descrição do problema observado — texto livre exibido na listagem e no detalhe.",
  correctiveActions: "Ações corretivas adotadas ou planejadas para a NC.",
  technicalOpinion: "Parecer técnico da Engenharia sobre a ocorrência.",
  problemTagsSection:
    "Tags compartilhadas do catálogo — selecione existentes ou crie novas (até 80 caracteres).",
  productsSection:
    "Produtos vinculados à NC — o código é obrigatório por linha; a descrição pode ser complementada pelos fatos TOTVS no detalhe.",
  context:
    "Situação da OV e estrutura dos produtos vêm dos fatos oficiais TOTVS via Engineering API.",
  history:
    "Auditoria append-only: criação e cada atualização com autor, data e campos alterados.",
  historyActor: "Usuário do Portal responsável por este evento de auditoria.",
  importPanel:
    "A importação substitui todo o acervo — execute o dry-run primeiro e confirme a substituição.",
} as const;
