import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { resolvePluginRoute } from "./pluginRoutes";
import {
  personColorKey,
  reservedPersonDetailPath,
  reservedSupplierDetailPath,
  supplierColorKey,
} from "./suppliesDirectory";

const dir = dirname(fileURLToPath(import.meta.url));

describe("suppliesDirectory reserved paths", () => {
  it("builds supplier 360 with store (positive) and without store (sibling)", () => {
    expect(reservedSupplierDetailPath("000123", "01")).toBe(
      "/apps/supplies/suppliers/000123/01",
    );
    expect(reservedSupplierDetailPath("000123")).toBe("/apps/supplies/suppliers/000123");
  });

  it("builds person path and does not invent a live route (negative)", () => {
    expect(reservedPersonDetailPath("JOSI")).toBe("/apps/supplies/people/JOSI");
    // Supplier detail went live in S3 — the reserved path now resolves.
    expect(resolvePluginRoute("/apps/supplies/suppliers/000123/01").view).toBe("supplier_detail");
    expect(resolvePluginRoute("/apps/supplies/people/JOSI").view).toBe("not_found");
    expect(resolvePluginRoute("/apps/supplies/suppliers").view).toBe("suppliers");
  });

  it("keeps color keys stable for the same identity", () => {
    expect(supplierColorKey("000123", "01")).toBe("000123|01");
    expect(personColorKey("JOSI", "000001")).toBe("000001");
    expect(personColorKey("JOSI")).toBe("JOSI");
  });

  it("supplier identity navigates only via canonical E14 link with code+store", () => {
    const identity = readFileSync(join(dir, "SuppliesDirectoryIdentity.tsx"), "utf8");
    expect(identity).toContain("SuppliesEntityAvatarLabel");
    expect(identity).toContain("supplierColorKey");
    expect(identity).toContain("personColorKey");
    // Navigation is allowed only through the canonical contract:
    // buildSupplierDetailPath + SuppliesEntityLink + navigatePluginPath.
    expect(identity).toContain("buildSupplierDetailPath");
    expect(identity).toContain("SuppliesEntityLink");
    expect(identity).toContain("navigatePluginPath");
    // Store is mandatory for the link — no assumed "01" or name-only nav.
    expect(identity).toContain("supplierStore");
    expect(identity).toMatch(/if \(!basePath \|\| !supplierCode \|\| !supplierStore\)/);
    // Forbidden shortcuts must never appear.
    expect(identity).not.toMatch(/window\.location|document\.location|useNavigate/);
    expect(identity).not.toMatch(/reservedSupplierDetailPath|reservedPersonDetailPath/);
  });

  it("operational consumers pass basePath to enable supplier navigation", () => {
    const featuresDir = join(dir, "..", "features");
    const consumers = [
      join(featuresDir, "purchase-orders", "PurchaseOrdersListTable.tsx"),
      join(featuresDir, "purchase-orders", "PurchaseOrdersCards.tsx"),
      join(featuresDir, "purchase-orders", "PurchaseOrderDetailPage.tsx"),
      join(featuresDir, "deliveries", "DeliveriesListTable.tsx"),
    ];
    for (const file of consumers) {
      const src = readFileSync(file, "utf8");
      const block = src.match(
        /<SuppliesSupplierIdentity[\s\S]*?\/>/,
      );
      expect(block, file).not.toBeNull();
      expect(block?.[0], file).toContain("basePath={basePath}");
      expect(block?.[0], file).toContain("store={");
      expect(block?.[0], file).toContain("code={");
    }
  });

});
