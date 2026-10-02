import { buildFinancialHref } from "./routeParser";
import type { FinancialBranch } from "../types";

export function invoiceSearchHref(input: {
  branch: FinancialBranch;
  invoiceNumber: string;
  invoiceValue: string;
  supplierCnpj: string;
}): string {
  return buildFinancialHref({
    subpluginId: "invoices",
    branch: input.branch,
    invoiceNumber: input.invoiceNumber.trim() || null,
    invoiceValue: input.invoiceValue.trim() || null,
    supplierCnpj: input.supplierCnpj.trim() || null,
    page: 1,
  });
}
