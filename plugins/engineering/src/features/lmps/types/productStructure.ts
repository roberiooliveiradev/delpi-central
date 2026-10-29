export type ProductStructureNode = {
  code?: string;
  product_code?: string;
  description?: string;
  type?: string;
  quantity?: number | null;
  unit?: string;
  components?: ProductStructureNode[];
  items?: ProductStructureNode[];
  [key: string]: unknown;
};

export type ProductStructureData = {
  root?: ProductStructureNode;
  items?: ProductStructureNode[];
  total?: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
};
