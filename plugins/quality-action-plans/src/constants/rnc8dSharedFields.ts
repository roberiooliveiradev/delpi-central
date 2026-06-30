export const RNC8D_SHARED_FIELD_LABELS = {
  clientNcRegistry: "Registro NC (cliente)",
  customer: "Cliente",
  productCode: "Código material",
  customerProductReference: "Referência do cliente",
  productDescription: "Descrição material",
  supplierBatch: "Lote fornecedor",
  reportedProblem: "Relato do problema",
} as const;

export type Rnc8dSharedIdentification = {
  client_nc_registry?: string;
  customer_name?: string;
  product_code?: string;
  product_description?: string;
  batch_number?: string;
  reported_problem?: string;
};

export const RNC8D_SHARED_MIRROR_HINT =
  "Editável no painel Problema — salve a identificação para atualizar o relatório 8D.";
