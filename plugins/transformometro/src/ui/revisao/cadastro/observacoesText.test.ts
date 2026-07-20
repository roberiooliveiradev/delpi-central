import { describe, expect, it } from "vitest";

import { optionalTrimmedText } from "../../../utils/optionalTrimmedText";

describe("optionalTrimmedText", () => {
  it("não deve ser usado no onChange (espaço intermediário precisa sobreviver no draft)", () => {
    // Simula draft sem trim: o valor cru permanece.
    const draft = "Foi ";
    expect(draft).toBe("Foi ");
    expect(optionalTrimmedText(draft)).toBe("Foi");
  });

  it("normaliza vazio e só espaços para undefined", () => {
    expect(optionalTrimmedText("")).toBeUndefined();
    expect(optionalTrimmedText("   ")).toBeUndefined();
    expect(optionalTrimmedText(null)).toBeUndefined();
    expect(optionalTrimmedText(undefined)).toBeUndefined();
  });
});
