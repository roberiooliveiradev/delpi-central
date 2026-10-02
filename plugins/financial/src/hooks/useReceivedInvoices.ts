import { fetchReceivedInvoices } from "../api/financialApi";
import { copy } from "../content/copy";
import type { ReceivedInvoicesPayload } from "../types";
import { useAsyncResource } from "./useAsyncResource";

export type ReceivedInvoiceFilters = {
  invoiceNumber: string | null;
  invoiceValue: string | null;
  supplierCnpj: string | null;
  page: number;
};

/** A consulta segue a URL aplicada. Digitar no campo não entra nesta chave. */
export function receivedInvoiceRequestKey(filters: ReceivedInvoiceFilters): string {
  return [filters.invoiceNumber ?? "", filters.invoiceValue ?? "", filters.supplierCnpj ?? "", filters.page].join(
    "|",
  );
}

export function useReceivedInvoices(filters: ReceivedInvoiceFilters) {
  const key = receivedInvoiceRequestKey(filters);
  return useAsyncResource<ReceivedInvoicesPayload>(
    (signal) =>
      fetchReceivedInvoices({
        invoiceNumber: filters.invoiceNumber,
        invoiceValue: filters.invoiceValue,
        supplierCnpj: filters.supplierCnpj,
        page: filters.page,
        signal,
      }),
    [key],
    copy.invoices.loadError,
  );
}
