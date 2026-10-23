import { httpGet, httpPost, suppliesApiUrl } from "../../../api/httpClient";
import type { ExistingSuppliersPage, SupplierCreationPreview } from "./types";

/** Prévia de cadastro por CNPJ — read-only, nunca persiste fornecedor. */
export function createSupplierPreview(
  taxId: string,
  signal?: AbortSignal,
): Promise<SupplierCreationPreview> {
  return httpPost<SupplierCreationPreview>(
    suppliesApiUrl("/suppliers/creation-preview"),
    { tax_id: taxId },
    { signal },
  );
}

/**
 * Paginação read-only dos cadastros existentes por CNPJ (X4.UX-R1.S8).
 * Consome o BFF canônico — nunca chama outro serviço nem provider externo.
 */
export function listExistingSuppliers(
  taxId: string,
  page: number,
  pageSize = 10,
  signal?: AbortSignal,
): Promise<ExistingSuppliersPage> {
  const params = new URLSearchParams({
    tax_id: taxId,
    page: String(page),
    page_size: String(pageSize),
  });
  return httpGet<ExistingSuppliersPage>(
    suppliesApiUrl("/suppliers/existing-suppliers?" + params.toString()),
    { signal },
  );
}
