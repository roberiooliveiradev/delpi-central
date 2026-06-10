export type OpsAbertaDetalhe = {
  filial: string;
  numero_op: string;
  produto: string;
  descricao_produto: string;
  tipo_produto: string;
  quantidade_op: number;
  quantidade_produzida: number;
  saldo_op: number;
  data_emissao_op: string | null;
  data_inicio_prevista_op: string | null;
  data_fim_prevista_op: string | null;
  armazem: string;
  observacao_op: string;
};

export type OpsAbertaResumo = {
  filial: string;
  produto: string;
  descricao_produto: string;
  tipo_produto: string;
  quantidade_ops_abertas: number;
  quantidade_total_ops: number;
  quantidade_total_produzida: number;
  saldo_total_ops: number;
  primeira_data_prevista_op: string | null;
  ultima_data_prevista_op: string | null;
};

export type OpsAbertasData = {
  items: OpsAbertaDetalhe[];
  resumo: OpsAbertaResumo[];
};
