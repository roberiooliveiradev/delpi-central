import { describe, expect, it } from "vitest";

import {
  pickPreferredCategoryField,
  resolveCategoryDisplayLabel,
  scoreCategoryFieldPreference,
} from "./categoryFieldPreference";

describe("categoryFieldPreference", () => {
  it("prefere label a code", () => {
    expect(scoreCategoryFieldPreference("label")).toBeGreaterThan(
      scoreCategoryFieldPreference("code"),
    );
    expect(
      pickPreferredCategoryField([{ field: "code" }, { field: "label" }, { field: "value" }]),
    ).toBe("label");
  });

  it("resolveCategoryDisplayLabel usa descrição quando categoria é código", () => {
    expect(
      resolveCategoryDisplayLabel({
        categoryKey: "FM",
        categoryField: "code",
        groupRows: [{ code: "FM", label: "FM - Falha de material" }],
      }),
    ).toBe("FM - Falha de material");
  });

  it("resolveCategoryDisplayLabel monta SIGLA - desc quando label não inclui código", () => {
    expect(
      resolveCategoryDisplayLabel({
        categoryKey: "FH",
        categoryField: "code",
        groupRows: [{ code: "FH", label: "Falha humana" }],
      }),
    ).toBe("FH - Falha humana");
  });

  it("não altera quando já usa o campo label", () => {
    expect(
      resolveCategoryDisplayLabel({
        categoryKey: "FM - Falha de material",
        categoryField: "label",
        groupRows: [{ code: "FM", label: "FM - Falha de material" }],
      }),
    ).toBe("FM - Falha de material");
  });
});
