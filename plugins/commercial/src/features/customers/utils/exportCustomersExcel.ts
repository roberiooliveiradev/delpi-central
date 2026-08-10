import { exportTableFormat } from "@delpi/plugin-ui/index";

import type { CustomerSummary } from "../types/customerSummary";
import { buildCustomersExportPayload } from "./customerExportPayload";
import type { CustomerColumnDef } from "./customerTableColumns";

function buildFilename(): string {
  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  const time = now.toTimeString().slice(0, 5).replace(":", "");
  return `carteira-clientes_${date}_${time}`;
}

export async function exportCustomersExcel(
  customers: CustomerSummary[],
  columns: CustomerColumnDef[],
): Promise<void> {
  if (customers.length === 0 || columns.length === 0) return;
  exportTableFormat(buildCustomersExportPayload(customers, columns), "xlsx", {
    filename: buildFilename(),
  });
}
