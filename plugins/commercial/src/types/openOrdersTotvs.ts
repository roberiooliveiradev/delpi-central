import type { LineOpForecast } from "../types/opForecast";

export type OpenOrdersTotvsSummary = {
  total_linhas: number;
  valor_total_aberto: number;
  itens_com_estoque: number;
  itens_estoque_parcial: number;
  linhas_em_atraso: number;
};

export type OpenOrdersTotvsItem = {
  nome_cliente: string;
  tipo_entidade: string;
  tipo_pedido: string;
  pedido_cliente: string;
  filial: string;
  pedido: string;
  linha: string;
  produto: string;
  codigo_cliente: string;
  /** Código Protheus do cliente/fornecedor (SC5.C5_CLIENTE). */
  codigo_cadastro: string;
  /** Loja Protheus do cliente/fornecedor (SC5.C5_LOJACLI). */
  loja_cadastro: string;
  quantidade: number;
  entregue: number;
  saldo: number;
  data_despacho: string | null;
  data_entrega: string | null;
  no_estoque: number;
  /** Estoque efetivamente reservado para a linha após alocação FIFO por produto/filial. */
  estoque_alocado?: number;
  previsao_op?: LineOpForecast;
  preco_venda: number;
  valor_aberto: number;
  /**
   * Número da OV (AD1_NROPOR) quando a API enriquecer o vínculo pedido↔oportunidade.
   * Sem o campo, o detalhe resolve via GET /commercial/proposals?search=pedido (não path /{pedido}).
   */
  proposal_number?: string | null;
};

export type OpenOrdersTotvsData = {
  items: OpenOrdersTotvsItem[];
  summary: OpenOrdersTotvsSummary;
  portfolio?: {
    empty?: boolean;
    message?: string | null;
    seller_id?: string | null;
  };
};
