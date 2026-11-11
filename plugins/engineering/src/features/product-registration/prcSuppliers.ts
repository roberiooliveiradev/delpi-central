/** PRC-REF-023-F03 — a implementação canônica migró para
 * `@delpi/plugin-ui` (`utils/prcProductRegistration`), fonte única
 * compartilhada entre Portal Engenharia e Minhas Solicitações. Shim
 * de compatibilidade dos imports existentes. */

/** @deprecated use duplicateDraftRowIds — mantido para testes legados. */
export function duplicateSupplierIndexes(rows: SupplierRow[]): Set<number> {
  const dups = duplicateDraftRowIds(rows);
  const out = new Set<number>();
  rows.forEach((r, i) => {
    if (dups.has(r.rowId)) out.add(i);
  });
  return out;
}

import {
  duplicateDraftRowIds,
  emptySupplierRow,
  findRowWithOfficialKey,
  newSupplierRowId,
  officialSupplierRow,
  supplierHitLabel,
  supplierHitMain,
  supplierHitSecondary,
  supplierOfficialKey,
  supplierRowsToPayload,
  toSupplierRows,
  type SupplierRow,
  type SupplierRowOrigin,
} from "@delpi/plugin-ui/index";
export {
  duplicateDraftRowIds,
  emptySupplierRow,
  findRowWithOfficialKey,
  newSupplierRowId,
  officialSupplierRow,
  supplierHitLabel,
  supplierHitMain,
  supplierHitSecondary,
  supplierOfficialKey,
  supplierRowsToPayload,
  toSupplierRows,
  type SupplierRow,
  type SupplierRowOrigin,
};
