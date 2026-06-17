export const ITEM_COLUMN_KEYS = [
  "item",
  "produto",
  "descricao",
  "referencia_cliente",
  "ncm",
  "quantidade",
  "valor_bruto",
  "valor_liquido",
  "total",
  "prazo",
  "lote_minimo",
] as const;

export type PropostaComercialItemColumnKey = (typeof ITEM_COLUMN_KEYS)[number];

export const RESUMO_LABEL_KEYS = [
  "numero_ov",
  "data",
  "versao",
  "total_r_mil",
  "empresa",
  "cliente",
] as const;

export type PropostaComercialResumoLabelKey = (typeof RESUMO_LABEL_KEYS)[number];

export const DEFAULT_ITEM_COLUMN_LABELS: Record<PropostaComercialItemColumnKey, string> = {
  item: "Item",
  produto: "Produto",
  descricao: "Descrição",
  referencia_cliente: "Ref. cliente",
  ncm: "NCM",
  quantidade: "Qtd.",
  valor_bruto: "Valor bruto R$/mil",
  valor_liquido: "Valor líquido R$/mil",
  total: "Total R$/mil",
  prazo: "Prazo",
  lote_minimo: "Lote mín.",
};

export const DEFAULT_RESUMO_LABELS: Record<PropostaComercialResumoLabelKey, string> = {
  numero_ov: "Nº OV",
  data: "Data",
  versao: "Versão",
  total_r_mil: "Total R$/mil",
  empresa: "Empresa",
  cliente: "Cliente",
};

export const DEFAULT_TOTAL_PROPOSTA_LABEL = "Total da proposta";

export type PropostaComercialRotulosDraft = {
  colunas_itens: Record<PropostaComercialItemColumnKey, string>;
  resumo: Record<PropostaComercialResumoLabelKey, string>;
  total_proposta: string;
};

export function buildDefaultRotulosDraft(): PropostaComercialRotulosDraft {
  return {
    colunas_itens: { ...DEFAULT_ITEM_COLUMN_LABELS },
    resumo: { ...DEFAULT_RESUMO_LABELS },
    total_proposta: DEFAULT_TOTAL_PROPOSTA_LABEL,
  };
}
