export type OpAllocationEntry = {
  numero_op: string;
  saldo_op_total: number;
  saldo_alocado: number;
  data_fim_prevista_op: string | null;
  observacao_op: string;
  /** Quantidade planejada da OP (C2_QUANT). */
  quantidade_op: number;
  /** Quantidade já produzida (C2_QUJE). */
  quantidade_produzida: number;
  data_emissao_op: string | null;
  data_inicio_prevista_op: string | null;
  armazem: string;
  descricao_produto: string;
};

export type LineOpForecastKind =
  | "estoque"
  | "sem_op"
  | "coberto"
  | "parcial"
  | "sem_data";

export type LineOpForecast = {
  kind: LineOpForecastKind;
  saldoNecessarioProducao: number;
  saldoCobertoPorOp: number;
  saldoFaltanteProducao: number;
  previsaoData: string | null;
  previsaoLabel: string;
  opsUtilizadas: OpAllocationEntry[];
};
