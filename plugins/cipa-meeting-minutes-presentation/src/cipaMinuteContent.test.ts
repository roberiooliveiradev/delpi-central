import { describe, expect, it } from "vitest";

import { collapseNbspRuns, formatMeetingDateLong, isHtmlEmpty } from "./cipaMinuteContent";

describe("cipaMinuteContent", () => {
  it("detecta HTML vazio", () => {
    expect(isHtmlEmpty("<p></p>")).toBe(true);
    expect(isHtmlEmpty("<p>Olá</p>")).toBe(false);
  });

  it("colapsa runs de nbsp", () => {
    expect(collapseNbspRuns("<p>a&nbsp;&nbsp;b</p>")).toBe("<p>a b</p>");
  });

  it("formata data longa pt-BR", () => {
    expect(formatMeetingDateLong("2026-07-16")).toBe("16 de julho de 2026");
  });
});
