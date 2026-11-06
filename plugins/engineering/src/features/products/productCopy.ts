/** Copy PT-BR da feature Produtos — labels de UI, hints de ajuda
 * (FieldLabel/HelpTooltip) e textos de estado honesto. Nenhum conteúdo
 * inventa semântica: hints descrevem o contrato oficial da fonte. */

export const PRODUCT_COPY = {
  listTitle: "Catálogo de produtos",
  listDescription:
    "Consulte produtos, estruturas, fornecedores, aplicações e desenhos técnicos em um só lugar.",
  detailTitle: "Ficha do Produto",
  breadcrumbBack: "Produtos",
  emptyList: "Nenhum produto encontrado para os filtros aplicados.",
  notFound: "Produto não encontrado no catálogo oficial.",
  forbidden:
    "Você não tem permissão para consultar produtos na fonte oficial.",
  viewMode: "Visualizar",
  editBlocked:
    "Edição indisponível — não existe contrato de escrita oficial para o cadastro de produtos (doc 63 §2.8).",
  tabs: {
    overview: "Visão geral",
    structure: "Estrutura",
    whereUsed: "Onde é usado",
    suppliers: "Fornecedores",
    drawings: "Desenhos",
    history: "Histórico",
  },
} as const;

export const PRODUCT_HELP = {
  search:
    "Busca reativa no catálogo oficial (TOTVS SB1) — os filtros disparam a consulta automaticamente.",
  productType:
    "Tipos do produto (SB1.B1_TIPO) — selecione um ou mais valores oficiais (ex.: MP, PI, PA).",
  groups:
    "Grupos do produto (SB1.B1_GRUPO) — selecione um ou mais códigos oficiais; a busca combina com OU.",
  clearFilters:
    "Remove todos os filtros e parâmetros da URL, restaurando a primeira página.",
  nonInformativeDescription:
    "Valor oficial gravado no cadastro (SB1.B1_DESC) sem conteúdo descritivo.",
  code: "Código DELPI do produto no catálogo oficial (SB1.B1_COD).",
  description: "Descrição cadastral do produto (SB1.B1_DESC).",
  type: "Tipo do produto no cadastro TOTVS (ex.: MP, PI, PA).",
  group: "Grupo de produtos (SB1.B1_GRUPO).",
  unit: "Unidade de medida principal (SB1.B1_UM).",
  active: "Indicador de cadastro ativo na fonte oficial.",
  blocked: "Indicador de bloqueio cadastral (SB1.B1_MSBLQL).",
  drawingCode: "Código do desenho do cliente (SB1.B1_CODDES).",
  revision: "Revisão cadastral atual do produto (SB1.B1_REVATU).",
  revisionDate: "Data da última revisão cadastral (SB1.B1_UREV).",
  structure:
    "Estrutura/BOM oficial do produto (SG1) — componentes diretos e dependentes, conforme vigência da fonte.",
  whereUsed:
    "Produtos pai que consomem este item — BOM reversa oficial (SG1).",
  suppliers:
    "Vínculos produto × fornecedor oficiais (SA5) — sem dados de preço.",
  drawings:
    "Desenho técnico localizado no acervo oficial do file server — mesmo contrato do Cockpit do Operador.",
  history:
    "Revisão cadastral oficial e histórico disponível — cada seção indica sua fonte e seu estado.",
  leadTime:
    "Prazo de entrega cadastrado e estatística real observada no vínculo.",
  editMode:
    "O modo Editar só é habilitado quando existe contrato de escrita oficial e autorização efetiva.",
} as const;

export const PRODUCT_TYPE_LABELS: Record<string, string> = {
  MP: "Matéria-prima",
  PI: "Produto intermediário",
  PA: "Produto acabado",
  BN: "Beneficiamento",
  SV: "Serviço",
};

export function productTypeLabel(type: string | null): string {
  if (!type) return "—";
  return PRODUCT_TYPE_LABELS[type] ?? type;
}

/** Descrições placeholder gravadas na fonte oficial (ex.: "#", "###")
 * são exibidas como estão — sem inventar texto — mas sinalizadas como
 * não informativas para a UI não as confundir com descrição real. */
const NON_INFORMATIVE_DESCRIPTION = /^#+\s*$/;

export type ProductDescriptionDisplay = {
  text: string;
  informative: boolean;
};

export function productDescriptionDisplay(
  description: string | null | undefined,
): ProductDescriptionDisplay {
  const text = (description ?? "").trim();
  if (!text) return { text: "—", informative: false };
  if (NON_INFORMATIVE_DESCRIPTION.test(text)) {
    return { text, informative: false };
  }
  return { text, informative: true };
}

export function formatProductDate(
  value: string | null | undefined,
): string {
  if (!value) return "—";
  const text = value.slice(0, 10);
  const [y, m, d] = text.split("-");
  return y && m && d ? `${d}/${m}/${y}` : value;
}

export function formatProductDateTime(
  value: string | null | undefined,
): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return formatProductDate(value);
  return date.toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

export function formatBytes(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value))
    return "—";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function productStatusLabel(product: {
  active?: string | null;
  blocked?: string | null;
}): string {
  const blocked = (product.blocked ?? "").trim().toUpperCase();
  if (blocked === "1" || blocked === "S" || blocked === "SIM")
    return "Bloqueado";
  const active = (product.active ?? "").trim().toUpperCase();
  if (active === "0" || active === "N" || active === "NAO")
    return "Inativo";
  return "Ativo";
}
