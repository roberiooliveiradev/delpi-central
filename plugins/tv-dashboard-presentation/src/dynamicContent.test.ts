import { describe, expect, it } from "vitest";

import {
  DYNAMIC_CONTENT_KIND_CATALOG,
  dataRefToDynamicContent,
  dynamicContentToDataRef,
  isDynamicContentKindImplemented,
} from "./dynamicContent";

describe("dynamicContent", () => {
  it("catálogo declara data_field implementado e scaffolds não", () => {
    expect(DYNAMIC_CONTENT_KIND_CATALOG.map((item) => item.kind)).toEqual([
      "data_field",
      "conditional_text",
      "expression",
    ]);
    expect(isDynamicContentKindImplemented("data_field")).toBe(true);
    expect(isDynamicContentKindImplemented("conditional_text")).toBe(false);
    expect(isDynamicContentKindImplemented("expression")).toBe(false);
  });

  it("converte dataRef ↔ spec data_field", () => {
    const ref = { field: "oee", format: "percent" as const };
    const spec = dataRefToDynamicContent(ref);
    expect(spec).toEqual({ kind: "data_field", dataRef: ref });
    expect(dynamicContentToDataRef(spec)).toEqual(ref);
    expect(
      dynamicContentToDataRef({ kind: "conditional_text", label: "x" }),
    ).toBeNull();
  });
});
