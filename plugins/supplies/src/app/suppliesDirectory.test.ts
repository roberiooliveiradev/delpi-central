import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { resolvePluginRoute } from "./pluginRoutes";
import { personColorKey, supplierColorKey } from "./suppliesDirectory";

const dir = dirname(fileURLToPath(import.meta.url));

describe("suppliesDirectory routes", () => {
  it("canonical detail routes resolve; reserved /people/:code stays not_found", () => {
    // Supplier detail went live in S3; user profile in USERS.PROFILE.S1.
    expect(resolvePluginRoute("/apps/supplies/suppliers/000123/01").view).toBe("supplier_detail");
    expect(resolvePluginRoute("/apps/supplies/people/JOSI").view).toBe("not_found");
    expect(resolvePluginRoute("/apps/supplies/suppliers").view).toBe("suppliers");
    expect(resolvePluginRoute("/apps/supplies/users/u-1").view).toBe("user_profile");
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

  it("person identity navigates only to the canonical user profile when authorized", () => {
    const identity = readFileSync(join(dir, "SuppliesDirectoryIdentity.tsx"), "utf8");
    // Canonical contract: buildUserProfileHref + SuppliesEntityLink +
    // navigatePluginPath, gated by proven user_id + canAccessUserProfile.
    expect(identity).toContain("buildUserProfileHref");
    expect(identity).toContain("canAccessUserProfile");
    expect(identity).toContain("navigatePluginPath");
    expect(identity).toContain("sp-person-identity-link");
    // No link without a proven Core identifier or basePath.
    expect(identity).toMatch(/if \(!basePath \|\| !targetUserId\) return label;/);
    // Never navigate from name/protheus id, and never invent another route.
    expect(identity).not.toMatch(/window\.location|document\.location|useNavigate/);
    expect(identity).not.toMatch(/\/users\/\$\{person/);
  });

  it("person consumers pass basePath to enable profile navigation", () => {
    const featuresDir = join(dir, "..", "features");
    const consumers = [
      join(featuresDir, "purchase-requests", "PurchaseRequestsListTable.tsx"),
      join(featuresDir, "purchase-requests", "PurchaseRequestsCards.tsx"),
      join(featuresDir, "purchase-requests", "PurchaseRequestDetailPage.tsx"),
    ];
    for (const file of consumers) {
      const src = readFileSync(file, "utf8");
      const block = src.match(/<SuppliesPersonIdentity[\s\S]*?\/>/);
      expect(block, file).not.toBeNull();
      expect(block?.[0], file).toContain("basePath={basePath}");
    }
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
