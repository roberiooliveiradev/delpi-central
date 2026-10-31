export type ProductStructureNode = {
  code?: string | null;
  product_code?: string | null;
  description?: string | null;
  type?: string | null;
  quantity?: number | null;
  unit?: string | null;
  components?: ProductStructureNode[] | null;
  items?: ProductStructureNode[] | null;
  /** Consulta reversa (where-used) — filhos vivem em `parents`. */
  parents?: ProductStructureNode[] | null;
  [key: string]: unknown;
};

export type ProductStructureData = {
  root?: ProductStructureNode | null;
  items?: ProductStructureNode[] | null;
  total?: number | null;
  page?: number | null;
  page_size?: number | null;
  total_pages?: number | null;
};
