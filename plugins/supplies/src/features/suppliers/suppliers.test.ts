import { describe, expect, it } from "vitest";

import {
  buildSupplierCreatePath,
  buildSupplierDetailPath,
  resolvePluginRoute,
} from "../../app/pluginRoutes";
import {
  buildUrlSearch,
  classifyWriteOutcome,
  createDefaultQuery,
  diffEditableFields,
  formatTaxIdMasked,
  hasActiveFilters,
  parseQueryFromSearch,
} from "./query";

describe("supplier routes", () => {
  it("resolves the suppliers list", () => {
    expect(resolvePluginRoute("/apps/supplies/suppliers").view).toBe("suppliers");
  });

  it("resolves supplier create before detail", () => {
    const route = resolvePluginRoute("/apps/supplies/suppliers/new");
    expect(route.view).toBe("supplier_create");
  });

  it("resolves supplier detail with code/store preserving leading zeros", () => {
    const route = resolvePluginRoute("/apps/supplies/suppliers/001234/01");
    expect(route.view).toBe("supplier_detail");
    expect(route.supplierCode).toBe("001234");
    expect(route.supplierStore).toBe("01");
    expect(buildSupplierDetailPath("001234", "01")).toBe(
      "/apps/supplies/suppliers/001234/01",
    );
    expect(buildSupplierCreatePath()).toBe("/apps/supplies/suppliers/new");
  });

  it("rejects non-numeric detail segments", () => {
    expect(resolvePluginRoute("/apps/supplies/suppliers/abc/01").view).toBe(
      "not_found",
    );
  });
});

describe("suppliers query", () => {
  it("round-trips search params through the URL", () => {
    const parsed = parseQueryFromSearch("?query=ferro&state=SC&blocked=1&page=3&page_size=50");
    expect(parsed.query).toBe("ferro");
    expect(parsed.state).toBe("SC");
    expect(parsed.blocked).toBe("1");
    expect(parsed.page).toBe(3);
    expect(parsed.page_size).toBe(50);
    expect(buildUrlSearch(parsed)).toBe("?query=ferro&state=SC&blocked=1&page=3&page_size=50");
  });

  it("sanitizes invalid values to defaults", () => {
    const parsed = parseQueryFromSearch("?blocked=yes&page=-2&page_size=7");
    expect(parsed).toEqual(createDefaultQuery());
    expect(hasActiveFilters(parsed)).toBe(false);
    expect(buildUrlSearch(parsed)).toBe("");
  });
});

describe("supplier edit diff", () => {
  const current = { supplier_name: "DELPI", supplier_short_name: "DELPI" };

  it("detects a single changed field", () => {
    const diff = diffEditableFields(current, {
      supplier_name: "DELPI NOVA",
      supplier_short_name: "DELPI",
    });
    expect(diff).toEqual([
      { field: "supplier_name", before: "DELPI", after: "DELPI NOVA" },
    ]);
  });

  it("detects both fields changed together", () => {
    const diff = diffEditableFields(current, {
      supplier_name: "A",
      supplier_short_name: "B",
    });
    expect(diff).toHaveLength(2);
  });

  it("returns empty when nothing changed", () => {
    expect(diffEditableFields(current, current)).toEqual([]);
  });
});

describe("write outcome classification", () => {
  it("never equates acknowledged with persisted", () => {
    expect(classifyWriteOutcome({ acknowledged: true }, 200)).toBe("acknowledged");
    expect(
      classifyWriteOutcome({ acknowledged: true, persistence_proven: true }, 200),
    ).toBe("persistence_confirmed");
  });

  it("classifies gate-off as write_disabled", () => {
    expect(
      classifyWriteOutcome(
        { outcome: "write_disabled", code: "PROTHEUS_SUPPLIER_UPDATE_DISABLED" },
        503,
      ),
    ).toBe("write_disabled");
    expect(
      classifyWriteOutcome(
        { code: "PROTHEUS_SUPPLIER_CREATE_DISABLED" },
        503,
      ),
    ).toBe("write_disabled");
  });

  it("classifies rejection and indeterminate outcomes", () => {
    expect(classifyWriteOutcome(undefined, 422)).toBe("rejected");
    expect(classifyWriteOutcome({}, 504)).toBe("indeterminate");
    expect(classifyWriteOutcome(undefined, undefined)).toBe("indeterminate");
  });
});

describe("tax id masking", () => {
  it("formats a CNPJ when not masked", () => {
    expect(formatTaxIdMasked("01234567000199", false)).toBe("01.234.567/0001-99");
  });

  it("never renders masked CPF digits", () => {
    expect(formatTaxIdMasked("***********", true)).toBe("••••••");
    expect(formatTaxIdMasked(null, true)).toBe("—");
  });
});
