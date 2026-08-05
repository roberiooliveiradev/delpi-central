export type OpenOrderItem = {
  nome_cliente: string;
  pedido: string;
  produto: string;
  quantidade: number;
  saldo?: number;
  filial: string;
  tipo_pedido?: string;
  codigo_cadastro?: string;
  loja_cadastro?: string;
  status?: string;
};

export type OpenOrdersSummary = {
  total_linhas?: number;
  valor_total_aberto?: number;
};

export type OpenOrdersData = {
  items: OpenOrderItem[];
  summary?: OpenOrdersSummary;
  portfolio?: {
    empty?: boolean;
    message?: string | null;
    seller_id?: string | null;
  };
};
