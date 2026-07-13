/** Alinhado a shared/api-delpi-envelope/types.ts */

export type ApiDelpiResponseMeta = {
  dataVersion?: string;
  operationId?: string;
  entity?: string;
  shape?: string;
};

export type ApiSuccessResponse<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: ApiDelpiResponseMeta;
};

export function unwrapApiDelpiEnvelope<T>(
  response: ApiSuccessResponse<T>,
  fallbackMessage: string,
): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}

export type InspecoesProcessoResumo = {
  filial: string;
  unidade: string;
  qtde_ops: number;
  qtde_ensaios: number;
  qtde_ensaios_aprovados: number;
  qtde_ensaios_reprovados: number;
  qtde_ensaios_tolerancia: number;
  qtde_ops_aprovadas: number;
  qtde_ops_reprovadas: number;
  qtde_ops_tolerancia: number;
  qtde_ops_nao_identificadas: number;
  qtde_produtos: number;
  qtde_operacoes: number;
  qtde_ensaiadores: number;
  primeira_data_medicao: string | null;
  ultima_data_medicao: string | null;
  percentual_ops_aprovadas: number;
  percentual_ops_reprovadas: number;
  percentual_ensaios_aprovados: number;
  percentual_ensaios_reprovados: number;
};

export type InspecoesProcessoPorProdutoItem = {
  filial: string;
  unidade: string;
  codigo_produto: string;
  descricao_produto: string;
  revisao_produto: string;
  qtde_ops: number;
  qtde_ensaios: number;
  qtde_ensaios_aprovados: number;
  qtde_ensaios_reprovados: number;
  qtde_ensaios_tolerancia: number;
  qtde_ops_aprovadas: number;
  qtde_ops_reprovadas: number;
  qtde_ops_tolerancia: number;
  qtde_ensaios_distintos: number;
  qtde_operacoes: number;
  qtde_ensaiadores: number;
  primeira_data_medicao: string | null;
  ultima_data_medicao: string | null;
  percentual_ops_aprovadas: number;
  percentual_ops_reprovadas: number;
  percentual_ensaios_aprovados: number;
  percentual_ensaios_reprovados: number;
};

export type InspecoesProcessoPorEnsaiadorItem = {
  filial: string;
  unidade: string;
  matricula_ensaiador: string;
  nome_ensaiador: string;
  login_ensaiador: string | null;
  qtde_ops: number;
  qtde_ensaios: number;
  qtde_ensaios_aprovados: number;
  qtde_ensaios_reprovados: number;
  qtde_ensaios_tolerancia: number;
  qtde_ops_aprovadas: number;
  qtde_ops_reprovadas: number;
  qtde_produtos: number;
  qtde_operacoes: number;
  qtde_ensaios_distintos: number;
  primeira_data_medicao: string | null;
  ultima_data_medicao: string | null;
  percentual_ops_aprovadas: number;
  percentual_ops_reprovadas: number;
  percentual_ensaios_aprovados: number;
  percentual_ensaios_reprovados: number;
};

export type InspecoesProcessoHistoricoItem = {
  filial: string;
  unidade: string;
  ordem_producao: string;
  codigo_produto: string;
  descricao_produto: string;
  revisao_produto: string;
  quantidade_op: number;
  chave_cabecalho_inspecao: string;
  origem_inspecao: string;
  qtde_ensaios: number;
  qtde_ensaios_aprovados: number;
  qtde_ensaios_reprovados: number;
  qtde_ensaios_tolerancia: number;
  qtde_operacoes: number;
  qtde_ensaiadores: number;
  resultado_inspecao_codigo: string;
  resultado_inspecao: string;
  primeira_data_medicao: string | null;
  ultima_data_medicao: string | null;
  ultima_hora_medicao: string | null;
  matricula_ultimo_ensaiador: string;
  nome_ultimo_ensaiador: string;
};

export type InspecoesProcessoHistoricoResponse = {
  items: InspecoesProcessoHistoricoItem[];
  page: number;
  page_size: number;
  has_next: boolean;
};

export type FetchHistoricoParams = {
  branch: string;
  page?: number;
  page_size?: number;
  ordem_producao?: string;
  codigo_produto?: string;
  resultado?: "A" | "R" | "T";
  data_inicio?: string;
  data_fim?: string;
  signal?: AbortSignal;
};

export type InspecoesProcessoHistoricoDetalheItem = {
  inspecao_id: string;
  ensaio_id: string;
  filial: string;
  unidade: string;
  ordem_producao: string;
  codigo_produto: string;
  descricao_produto: string;
  revisao_produto: string;
  roteiro: string;
  operacao: string;
  recurso: string;
  ferramenta: string;
  centro_trabalho: string;
  descricao_operacao: string;
  laboratorio: string;
  codigo_ensaio: string;
  nome_ensaio: string;
  especificacao_textual: string | null;
  valor_nominal: string | null;
  limite_inferior_especificacao: string | null;
  limite_superior_especificacao: string | null;
  limite_inferior_controle: string | null;
  limite_superior_controle: string | null;
  regra_min_max: string | null;
  unidade_especificacao: string | null;
  especificacao_esperada: string | null;
  medicao_textual: string | null;
  medicao_numerica_a: number | null;
  medicao_numerica_n: number | null;
  medicao_numerica: string | null;
  modo_medicao_numerica: string | null;
  fonte_medicao: string | null;
  resultado_codigo: string;
  resultado: string;
  data_medicao: string | null;
  hora_medicao: string | null;
  matricula_ensaiador: string;
  nome_ensaiador: string;
  chave_medicao: string | null;
  qpr_recno: number | null;
};

export type InspecoesProcessoHistoricoDetalheResponse = {
  cabecalho: InspecoesProcessoHistoricoItem;
  items: InspecoesProcessoHistoricoDetalheItem[];
  page: number;
  page_size: number;
  has_next: boolean;
};

export type FetchHistoricoDetalheParams = {
  branch: string;
  ordem_producao: string;
  page?: number;
  page_size?: number;
  signal?: AbortSignal;
};

export type InspecoesProcessoAuditoriaApontamentoItem = {
  filial: string;
  cod_operador: string;
  login_operador: string;
  nome_operador: string;
  op: string;
  produto: string;
  descricao_produto: string;
  revisao_produto: string;
  operacao: string;
  centro_trabalho: string;
  data_producao: string | null;
  hora_inicio: string | null;
  hora_final: string | null;
  qtd_apontamentos: number;
  operador_inspecionou: boolean;
  tem_inspecao_na_op_operacao: boolean;
  tem_inspecao_amarrada: boolean;
  tem_inspecao_executada: boolean;
};

export type InspecoesProcessoAuditoriaApontamentosSummary = {
  operadores_pendentes: number;
  apontamentos_pendentes: number;
  ops_operacoes_pendentes: number;
  apontamentos_com_inspecao: number;
  apontamentos_total: number;
};

export type InspecoesProcessoAuditoriaApontamentosResponse = {
  summary: InspecoesProcessoAuditoriaApontamentosSummary;
  items: InspecoesProcessoAuditoriaApontamentoItem[];
  page: number;
  page_size: number;
  has_next: boolean;
  data: string;
};

export type FetchAuditoriaApontamentosParams = {
  branch: string;
  data?: string;
  page?: number;
  page_size?: number;
  signal?: AbortSignal;
};
