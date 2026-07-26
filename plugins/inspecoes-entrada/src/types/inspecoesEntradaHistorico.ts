export type InspecoesEntradaHistoricoItem = {
  branch: string;
  inspection_id: string;
  received_date: string | null;
  received_time: string | null;
  report_date: string | null;
  report_time: string | null;
  invoice_number: string;
  invoice_series: string;
  invoice_item: string;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  product_code: string;
  lot: string;
  supplier_lot: string;
  quantity: number;
  unit: string;
  status_code: string;
  inspection_status: string;
  result: string;
  report_code: string;
  approved_quantity: number | null;
  rejected_quantity: number | null;
  report_justification: string;
  inspector_registration: string;
  inspector_name: string;
  inspector_login: string;
  tests_count: number;
  failed_tests_count: number;
  is_approved: boolean;
  is_rejected: boolean;
};

export type HistoricoPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type HistoricoFiltersEcho = {
  result: string | null;
  start_date: string | null;
  end_date: string | null;
  supplier: string | null;
  product_code: string | null;
  inspector: string | null;
  invoice_number: string | null;
  lot: string | null;
};

export type InspecoesEntradaHistoricoData = {
  branch: string;
  items: InspecoesEntradaHistoricoItem[];
  pagination: HistoricoPagination;
  filters: HistoricoFiltersEcho;
};

export type HistoricoResultFilter = "" | "APROVADA" | "REJEITADA";

export type HistoricoFilters = {
  result: HistoricoResultFilter;
  start_date: string;
  end_date: string;
  supplier: string;
  product_code: string;
  inspector: string;
  invoice_number: string;
  lot: string;
};

export type FetchHistoricoParams = {
  branch: string;
  page: number;
  page_size: number;
  result?: string;
  start_date?: string;
  end_date?: string;
  supplier?: string;
  product_code?: string;
  inspector?: string;
  invoice_number?: string;
  lot?: string;
};
