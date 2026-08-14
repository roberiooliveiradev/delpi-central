import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function read(rel: string): string {
  return readFileSync(resolve(root, rel), "utf8");
}

describe("entity real links — call sites migrados", () => {
  it("tabelas principais usam CommercialEntityLink ou ActionButton href", () => {
    const files = [
      "src/components/OpenOrdersTable.tsx",
      "src/components/OpenOrdersLineCard.tsx",
      "src/components/OpenOrdersProductionDetailContent.tsx",
      "src/features/customers/components/CustomersTable.tsx",
      "src/features/customers/components/CustomerOrdersTable.tsx",
      "src/features/customers/billing/components/CustomerInvoicesTable.tsx",
      "src/features/proposals/ProposalsDocumentsTable.tsx",
      "src/features/analytics/components/CommercialProposalsTable.tsx",
      "src/features/analytics/AnalyticsTeamPage.tsx",
      "src/features/administration/AdministrationTeamPage.tsx",
      "src/features/seller-portfolios/SellerPortfoliosList.tsx",
    ];
    for (const file of files) {
      const source = read(file);
      const usesEntityLink = source.includes("CommercialEntityLink");
      const usesActionHref =
        source.includes("href={") && source.includes("ActionButton");
      expect(
        usesEntityLink || usesActionHref,
        `${file} deveria usar CommercialEntityLink ou ActionButton com href`,
      ).toBe(true);
      expect(source).toMatch(/title=\{|title=/);
    }
  });
});
