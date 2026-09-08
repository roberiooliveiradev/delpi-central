import { describe, expect, it } from "vitest";

import { ADMIN_HELP } from "./adminHelpTooltips";

describe("adminHelpTooltips", () => {
  it("cobre as seções principais do admin", () => {
    expect(ADMIN_HELP.overview.length).toBeGreaterThan(20);
    expect(ADMIN_HELP.overview).toMatch(/fila de atenção/i);
    expect(ADMIN_HELP.metrics).toMatch(/drill-down|atenção/i);
    expect(ADMIN_HELP.specialization).toMatch(/Studio/i);
    expect(ADMIN_HELP.fineTuneExportOnly).toMatch(/export/i);
  });

  it("não vaza paths técnicos de API", () => {
    const blob = Object.values(ADMIN_HELP).join(" ");
    expect(blob).not.toMatch(/\/admin\//);
    expect(blob).not.toMatch(/operationId/i);
  });
});
