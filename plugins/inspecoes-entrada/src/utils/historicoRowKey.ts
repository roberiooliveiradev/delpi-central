import type { InspecoesEntradaHistoricoItem } from "../types/inspecoesEntradaHistorico";

/** Chave de linha estável: Id_Inspecao pode colidir (fornecedor-produto-data-hora). */
export function historicoRowKey(
  item: Pick<
    InspecoesEntradaHistoricoItem,
    | "inspection_id"
    | "invoice_number"
    | "invoice_series"
    | "invoice_item"
    | "supplier_code"
    | "supplier_store"
    | "product_code"
    | "lot"
    | "report_date"
    | "report_time"
  >,
  index?: number,
): string {
  const parts = [
    item.inspection_id,
    item.invoice_number,
    item.invoice_series,
    item.invoice_item,
    item.supplier_code,
    item.supplier_store,
    item.product_code,
    item.lot,
    item.report_date,
    item.report_time,
  ].map((value) => String(value ?? "").trim());
  const base = parts.join("|");
  return index === undefined ? base : `${base}|${index}`;
}
