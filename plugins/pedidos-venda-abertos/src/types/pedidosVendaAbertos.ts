export type PedidosVendaAbertosSummary = {
  total_linhas: number;
  valor_total_aberto: number;
  itens_com_estoque: number;
  itens_estoque_parcial: number;
  linhas_em_atraso: number;
};

export type PedidosVendaAbertosItem = {
  nome_cliente: string;
  tipo_entidade: string;
  tipo_pedido: string;
  pedido_cliente: string;
  filial: string;
  pedido: string;
  linha: string;
  produto: string;
  codigo_cliente: string;
  quantidade: number;
  entregue: number;
  saldo: number;
  data_despacho: string | null;
  data_entrega: string | null;
  no_estoque: number;
  /** Estoque efetivamente reservado para a linha após alocação FIFO por produto/filial. */
  estoque_alocado?: number;
  preco_venda: number;
  valor_aberto: number;
};

export type PedidosVendaAbertosData = {
  items: PedidosVendaAbertosItem[];
  summary: PedidosVendaAbertosSummary;
};
