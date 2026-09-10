import { describe, expect, it } from "vitest";

import {
  getColorFamilyDefinition,
  listColorFamilies,
  resolveColorFamily,
} from "../index";

/**
 * Garante que o barrel `@delpi/plugin-ui/index` reexporta o Color Family Catalog.
 * Hosts MF (minha-delpi-chat) importam daqui — export ausente → runtime TypeError.
 */
describe("colorFamily barrel export (index)", () => {
  it("expõe resolveColorFamily como função", () => {
    expect(typeof resolveColorFamily).toBe("function");
    expect(resolveColorFamily("brand")).toEqual([
      "var(--mdc-chart-series-1)",
      "var(--mdc-chart-series-10)",
    ]);
  });

  it("expõe listColorFamilies e getColorFamilyDefinition", () => {
    expect(typeof listColorFamilies).toBe("function");
    expect(listColorFamilies()).toContain("categorical");
    expect(getColorFamilyDefinition("warm")?.id).toBe("warm");
  });
});
