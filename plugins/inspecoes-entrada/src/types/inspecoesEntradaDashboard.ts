export type InspecoesEntradaPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type InspecoesEntradaResumo = {
  branch: string;
  pending_inspections: number;
  inspected: number;
  approved_inspections: number;
  rejected_inspections: number;
  approval_rate: number;
  inspections_with_time: number;
  average_time_hours: number;
  average_time_days: number;
};

export type InspecoesEntradaPendente = {
  branch: string;
  received_date: string | null;
  received_time: string | null;
  invoice_number: string;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  product_code: string;
  product_description?: string | null;
  quantity: number;
  unit: string;
  status_code: string;
  inspection_status: string;
};

export type InspecoesEntradaPendentesResponse = {
  branch: string;
  items: InspecoesEntradaPendente[];
  pagination: InspecoesEntradaPagination;
};

export type InspecoesEntradaPendenteFornecedor = {
  branch: string;
  supplier_name: string;
  pending_count: number;
};

export type InspecoesEntradaPendentesFornecedorResponse = {
  branch: string;
  items: InspecoesEntradaPendenteFornecedor[];
  total_suppliers: number;
  total_pending: number;
};

export type InspecoesEntradaRejeitadaProduto = {
  branch: string;
  inspection_id: string;
  report_date: string | null;
  report_time: string | null;
  invoice_number: string;
  supplier_name: string;
  product_code: string;
  product_description?: string | null;
  lot: string;
  quantity: number;
  unit: string;
};

export type InspecoesEntradaRejeitadasProdutoResponse = {
  branch: string;
  items: InspecoesEntradaRejeitadaProduto[];
  total: number;
};
