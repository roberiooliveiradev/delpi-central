import { describe, expect, it } from "vitest";

import { collapseNbspRuns, formatDateBr, isHtmlEmpty } from "./htmlContent";

describe("htmlContent", () => {
  it("detecta html vazio", () => {
    expect(isHtmlEmpty("<p></p>")).toBe(true);
    expect(isHtmlEmpty("<p><br></p>")).toBe(true);
    expect(isHtmlEmpty("<p>Texto</p>")).toBe(false);
  });

  it("formata data ISO", () => {
    expect(formatDateBr("2026-07-16")).toBe("16/07/2026");
  });

  it("colapsa runs de nbsp coladas do Word", () => {
    expect(
      collapseNbspRuns("<p>1.<span>&nbsp;&nbsp;&nbsp;&nbsp; </span>Texto</p>"),
    ).toBe("<p>1.<span> </span>Texto</p>");
    expect(collapseNbspRuns("a&#160;\u00a0&nbsp;b")).toBe("a b");
  });

  it("preserva nbsp isolado", () => {
    expect(collapseNbspRuns("10&nbsp;km")).toBe("10&nbsp;km");
    expect(collapseNbspRuns(null)).toBe("");
  });
});
