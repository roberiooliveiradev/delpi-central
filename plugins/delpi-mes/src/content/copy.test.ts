import { describe, expect, it } from "vitest";

import { DELPI_MES_COPY } from "./copy";

describe("Delpi MES help content", () => {
  it("documents every foundation area and branch behavior", () => {
    expect(DELPI_MES_COPY.monitoring.title).toBe("Monitoramento Industrial");
    expect(DELPI_MES_COPY.downtimes.title).toBe("Paradas");
    expect(DELPI_MES_COPY.history.title).toBe("Histórico");
    expect(DELPI_MES_COPY.help.branch).toContain("URL");
  });
});
