import { httpPost, suppliesApiUrl } from "../../../api/httpClient";
import type { SupplierCreationPreview } from "./types";

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
