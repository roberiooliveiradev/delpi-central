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
    expect(resolvePluginRoute("/apps/supplies/suppliers/000123/01").view).toBe("not_found");
    expect(resolvePluginRoute("/apps/supplies/people/JOSI").view).toBe("not_found");
    expect(resolvePluginRoute("/apps/supplies/suppliers").view).toBe("suppliers");
  });

  it("keeps color keys stable for the same identity", () => {
    expect(supplierColorKey("000123", "01")).toBe("000123|01");
    expect(personColorKey("JOSI", "000001")).toBe("000001");
    expect(personColorKey("JOSI")).toBe("JOSI");
  });

  it("identity wrappers use kit label and never set href", () => {
    const identity = readFileSync(join(dir, "SuppliesDirectoryIdentity.tsx"), "utf8");
    expect(identity).toContain("SuppliesEntityAvatarLabel");
    expect(identity).toContain("supplierColorKey");
    expect(identity).toContain("personColorKey");
    expect(identity).not.toMatch(/href=/);
    expect(identity).not.toMatch(/reservedSupplierDetailPath|reservedPersonDetailPath/);
  });
});
