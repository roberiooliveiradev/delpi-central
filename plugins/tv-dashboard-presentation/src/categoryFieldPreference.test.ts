import { describe, expect, it } from "vitest";

import {
  pickPreferredCategoryField,
  resolveCategoryDisplayLabel,
  scoreCategoryFieldPreference,
} from "./categoryFieldPreference";

describe("categoryFieldPreference", () => {
  it("prefere code a label (eixo curto; descrição fica no campo label)", () => {
    expect(scoreCategoryFieldPreference("code")).toBeGreaterThan(
      scoreCategoryFieldPreference("label"),
    );
    expect(
      pickPreferredCategoryField([{ field: "label" }, { field: "code" }, { field: "value" }]),
    ).toBe("code");
  });

  it("resolveCategoryDisplayLabel usa descrição curta quando categoria é sigla", () => {
    expect(
      resolveCategoryDisplayLabel({
        categoryKey: "FM",
        categoryField: "code",
        groupRows: [{ code: "FM", label: "FM - Falha de material" }],
      }),
    ).toBe("FM - Falha de material");
  });

  it("resolveCategoryDisplayLabel monta SIGLA - desc curta", () => {
    expect(
      resolveCategoryDisplayLabel({
        categoryKey: "FH",
        categoryField: "code",
        groupRows: [{ code: "FH", label: "Falha humana" }],
      }),
    ).toBe("FH - Falha humana");
  });

  it("não cola descrição longa de matéria-prima no eixo (só o código)", () => {
    expect(
      resolveCategoryDisplayLabel({
        categoryKey: "10070821",
        categoryField: "code",
        groupRows: [
          {
            code: "10070821",
            label:
              "CABO PP CIRCULAR PVC/PVC 4X1.5MM2 CZ SPT/VDAR 90'C 600V DIAM EXT 8.20MM VIAS NUMERADAS UL/CSA",
          },
        ],
      }),
    ).toBe("10070821");
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
