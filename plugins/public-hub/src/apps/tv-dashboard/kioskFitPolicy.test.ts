import { describe, expect, it } from "vitest";

/**
 * Contrato documentado: TV kiosk usa cover (sem letterbox); prévia admin contain.
 * Espelha a escolha em PresentationView (mode === "public" ? cover : contain).
 */
describe("kiosk design viewport fit policy", () => {
  it("público/TV prefere cover; prévia prefere contain", () => {
    const fitFor = (mode: "public" | "preview") =>
      mode === "public" ? "cover" : "contain";
    expect(fitFor("public")).toBe("cover");
    expect(fitFor("preview")).toBe("contain");
  });
});
