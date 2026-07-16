import { describe, expect, it } from "vitest";

import { formatDateBr, isHtmlEmpty } from "./htmlContent";

describe("htmlContent", () => {
  it("detecta html vazio", () => {
    expect(isHtmlEmpty("<p></p>")).toBe(true);
    expect(isHtmlEmpty("<p><br></p>")).toBe(true);
    expect(isHtmlEmpty("<p>Texto</p>")).toBe(false);
  });

  it("formata data ISO", () => {
    expect(formatDateBr("2026-07-16")).toBe("16/07/2026");
  });
});
