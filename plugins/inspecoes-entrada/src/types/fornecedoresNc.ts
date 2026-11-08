export type FornecedorNc = {
  branch: string;
  code: string;
  code_display: string | null;
  revision: string;
  type_code: string;
  type_label: string | null;
  status_code: string | null;
  status_label: string | null;
  description: string | null;
  detailed_description: string | null;
  item_code: string | null;
  registered_date: string | null;
  occurrence_date: string | null;
  supplier_code: string | null;
  supplier_store: string | null;
  priority_label: string | null;
  returned_quantity: number | null;
};

export type FornecedoresNcResponse = {
  items: FornecedorNc[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type FornecedoresNcFilters = {
  branch: string;
  start_date: string;
  end_date: string;
  status?: string;
  item_code?: string;
  description?: string;
  page: number;
  page_size: number;
};
