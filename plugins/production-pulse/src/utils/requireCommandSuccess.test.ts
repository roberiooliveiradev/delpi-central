import { describe, expect, it } from "vitest";

import { requireCommandSuccess } from "./requireCommandSuccess";

describe("requireCommandSuccess", () => {
  it("aceita success=true (positivo)", () => {
    expect(() => requireCommandSuccess({ success: true, errorMessage: null }, "falhou")).not.toThrow();
  });

  it("propaga errorMessage quando success=false (irmão)", () => {
    expect(() =>
      requireCommandSuccess({ success: false, errorMessage: "Chip offline" }, "falhou"),
    ).toThrow("Chip offline");
  });

  it("usa fallback quando success=false sem mensagem (negativo)", () => {
    expect(() => requireCommandSuccess({ success: false, errorMessage: "  " }, "falhou")).toThrow(
      "falhou",
    );
    expect(() => requireCommandSuccess({ success: false }, "falhou")).toThrow("falhou");
  });
});
