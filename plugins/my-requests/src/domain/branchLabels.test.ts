import { describe, expect, it } from "vitest";

import { branchAriaLabel, branchShortLabel } from "./branchLabels";

describe("branchLabels", () => {
  it("mapeia 01→SC e 02→ES", () => {
    expect(branchShortLabel("01")).toBe("SC");
    expect(branchShortLabel("02")).toBe("ES");
    expect(branchShortLabel("99")).toBe("99");
  });

  it("expõe aria labels legíveis", () => {
    expect(branchAriaLabel("01")).toBe("Santa Catarina");
    expect(branchAriaLabel("02")).toBe("Espírito Santo");
  });
});
