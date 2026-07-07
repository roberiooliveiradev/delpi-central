import { describe, expect, it } from "vitest";

import {
  CHART_COLORS_DEPARTMENTAL,
  CHART_COLORS_LMPS,
  CHART_HEIGHT_DEFAULT,
} from "./chartColors";

describe("chartColors", () => {
  it("expõe paleta departamental com 6 cores", () => {
    expect(CHART_COLORS_DEPARTMENTAL).toHaveLength(6);
    expect(CHART_COLORS_DEPARTMENTAL[0]).toBe("#089bdb");
  });

  it("expõe paleta LMPs distinta", () => {
    expect(CHART_COLORS_LMPS).toHaveLength(3);
  });

  it("define altura padrão de gráfico", () => {
    expect(CHART_HEIGHT_DEFAULT).toBe(280);
  });
});
