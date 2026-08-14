/**
 * Export Excel da matriz org (carteira × carga) — E6.5, client-side.
 */
import { exportTableFormat } from "@delpi/plugin-ui/index";

import type { PortfolioLoadItem, SellerPortfolio } from "../types/portfolio";
import { buildOrgMatrixExportPayload } from "./orgMatrixExportPayload";

function buildFilename(): string {
  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  const time = now.toTimeString().slice(0, 5).replace(":", "");
  return `matriz-carteiras_${date}_${time}`;
}

export { buildOrgMatrixExportPayload } from "./orgMatrixExportPayload";

export async function exportOrgMatrixExcel(
  portfolios: readonly SellerPortfolio[],
  loadByPortfolioId: ReadonlyMap<string, PortfolioLoadItem> | undefined,
  directoryLabelFor: (userId: string | null | undefined, fallback?: string | null) => string,
): Promise<boolean> {
  if (portfolios.length === 0) return false;
  const payload = buildOrgMatrixExportPayload(
    portfolios,
    loadByPortfolioId,
    directoryLabelFor,
  );
  exportTableFormat(payload, "xlsx", { filename: buildFilename() });
  return true;
}
