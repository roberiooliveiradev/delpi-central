/**
 * Fonte única de rótulos e enums de fallback para parâmetros de dados no MFE TV Dashboard.
 * Preferir `meta`/OpenAPI da API quando disponível; estes mapas cobrem UI estável entre rotas.
 */

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
