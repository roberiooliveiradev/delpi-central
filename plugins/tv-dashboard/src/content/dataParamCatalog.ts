/**
 * Fonte única de rótulos e enums de fallback para parâmetros de dados no MFE TV Dashboard.
 * Preferir `meta`/OpenAPI da API quando disponível; estes mapas cobrem UI estável entre rotas.
 * Manter alinhado a `PARAM_LABELS_PT` / `PARAM_HINTS_PT` em
 * `scripts/generate_tv_data_routes_from_openapi.py`.
 */

export const PARAM_FIELD_LABELS: Record<string, string> = {
  branch: "Filial",
  branch_code: "Código da filial",
  filial_id: "ID da filial",
  periodDays: "Período (dias)",
  start_date: "Data início",
  end_date: "Data fim",
  date_start: "Data início",
  date_end: "Data fim",
  date_from: "Data início",
  date_to: "Data fim",
  data_inicial: "Data inicial",
  data_final: "Data final",
  issue_date_start: "Data de emissão (início)",
  issue_date_end: "Data de emissão (fim)",
  reference_date: "Data de referência",
  customer_segment: "Segmento",
  granularity: "Granularidade",
  limit: "Limite",
  top_limit: "Limite do ranking",
  top_n: "Top N",
  offset: "Deslocamento",
  page: "Página",
  page_size: "Tamanho da página",
  code: "Código",
  product_code: "Código do produto",
  item_code: "Código do item",
  work_center: "Centro de trabalho",
  department_id: "Departamento",
  sort_by: "Ordenar por",
  sort_dir: "Direção da ordenação",
  group_by: "Agrupar por",
  listing_type: "Tipo de listagem",
  loss_type: "Tipo de perda",
  stock_method: "Método de estoque",
  summary_only: "Somente resumo",
  include_qtd_pi: "Incluir quantidade PI",
  product_type: "Tipo de produto",
};

export const PARAM_FIELD_HINTS: Record<string, string> = {
  branch:
    "Código da filial no Protheus (ex.: 01 ou 02). Vazio usa o consolidado da rota, quando permitido.",
  branch_code: "Código da filial no Protheus (ex.: 01 ou 02).",
  filial_id:
    "Identificador da filial no cadastro. Prefira o código curto (01, 02) quando a rota aceitar branch.",
  periodDays: "Quantos dias para trás entram no cálculo (ex.: 30 = último mês até hoje).",
  granularity: "Como agrupar os pontos da série: day (dia), week (semana), month (mês) ou year (ano).",
  customer_segment:
    "Filtra clientes: weg (WEG) ou new_business (novos negócios). Vazio = todos os segmentos.",
  start_date:
    "Início do intervalo (AAAA-MM-DD). Em rotas com Período (dias), o sistema pode calcular automaticamente.",
  end_date:
    "Fim do intervalo (AAAA-MM-DD). Em rotas com Período (dias), o sistema pode calcular automaticamente.",
  date_start: "Data inicial do período consultado (AAAA-MM-DD).",
  date_end: "Data final do período consultado (AAAA-MM-DD).",
  date_from: "Data inicial do período consultado (AAAA-MM-DD).",
  date_to: "Data final do período consultado (AAAA-MM-DD).",
  data_inicial: "Data inicial do período consultado (AAAA-MM-DD).",
  data_final: "Data final do período consultado (AAAA-MM-DD).",
  issue_date_start: "Início do filtro pela data de emissão do documento (AAAA-MM-DD).",
  issue_date_end: "Fim do filtro pela data de emissão do documento (AAAA-MM-DD).",
  reference_date: "Data de referência usada no cálculo (AAAA-MM-DD).",
  page: "Número da página na listagem paginada.",
  page_size: "Quantidade de linhas por página.",
  limit: "Máximo de registros retornados pela API (ranking ou listagem truncada).",
  top_limit: "Quantidade máxima de itens no ranking.",
  top_n: "Quantidade de itens no Top N.",
  offset: "Quantos registros pular antes de retornar a página (paginação por deslocamento).",
  work_center: "Código do centro de trabalho (CT) no Protheus. Vazio = todos os centros.",
  department_id: "Identificador do departamento no painel IDD.",
  product_code: "Código do produto no Protheus (ex.: 90xxxxxx).",
  item_code: "Código do item/material no Protheus.",
  group_by: "Como agregar o resultado (geral, filial, produto etc.).",
  sort_by: "Campo usado para ordenar a listagem.",
  sort_dir: "Direção da ordenação: asc (crescente) ou desc (decrescente).",
  listing_type: "Filtro de tipo da listagem (ex.: Todos, LMP, Amostra).",
  loss_type: "Tipo de perda a considerar: refugo, scrap ou ambos.",
  stock_method: "Método de valorização/consulta de estoque.",
  summary_only: "Quando ativo, retorna só o resumo sem a lista detalhada.",
  include_qtd_pi: "Inclui quantidade de produto intermediário (PI) no resultado.",
  product_type: "Filtra por tipo: PA (acabado) ou PI (intermediário).",
};

export const ENUM_OPTION_LABELS: Record<string, Record<string, string>> = {
  granularity: { day: "Dia", week: "Semana", month: "Mês", year: "Ano" },
  customer_segment: { weg: "WEG", new_business: "Novos negócios" },
  loss_type: { refugo: "Refugo", scrap: "Scrap", both: "Ambos" },
  product_type: { PA: "Produto acabado (PA)", PI: "Produto intermediário (PI)" },
  sort_dir: { asc: "Crescente", desc: "Decrescente" },
  direction: { asc: "Crescente", desc: "Decrescente" },
  orderDir: { asc: "Crescente", desc: "Decrescente" },
  linked_sort_dir: { asc: "Crescente", desc: "Decrescente" },
  stock_method: {
    auto: "Automático",
    hybrid: "Híbrido",
    estimated: "Estimado",
    official_closure: "Fechamento oficial",
  },
  view: {
    by_material: "Por material",
    by_finished_product: "Por produto acabado",
    full: "Completo",
    summary: "Resumo",
  },
  orderBy: { horas: "Horas", custo: "Custo", data: "Data" },
  listing_type: { Todos: "Todos", LMP: "LMP", Amostra: "Amostra", Outro: "Outro" },
  group_by: { general: "Geral", branch: "Filial", product: "Produto" },
};

/** Enums de UI quando o OpenAPI não declara `enum` (valores estáveis entre rotas). */
export const UI_FALLBACK_ENUMS: Record<string, Array<string | number>> = {
  sort_dir: ["asc", "desc"],
  direction: ["asc", "desc"],
  orderDir: ["asc", "desc"],
  linked_sort_dir: ["asc", "desc"],
  product_type: ["PA", "PI"],
  loss_type: ["refugo", "scrap", "both"],
  stock_method: ["auto", "hybrid", "estimated", "official_closure"],
};

/** Rótulo PT canônico; ignora rótulo EN residual do OpenAPI/humanize. */
export function resolveParamFieldLabel(key: string, schemaLabel?: string): string {
  return PARAM_FIELD_LABELS[key] ?? schemaLabel?.trim() ?? key;
}

export function resolveParamFieldHint(key: string, schemaDescription?: string): string | undefined {
  const fromCatalog = PARAM_FIELD_HINTS[key]?.trim();
  if (fromCatalog) return fromCatalog;
  const fromSchema = schemaDescription?.trim();
  return fromSchema || undefined;
}
