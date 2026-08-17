import { describe, expect, it } from "vitest";

import { buildAnalyticsOtdLinePath } from "../../app/pluginNavigation";
import { otdLineLinkTitle } from "../../content/entityLinkHints";

describe("E4.S1 OTD order links", () => {
  it("monta href de linha OTD e title", () => {
    const href = buildAnalyticsOtdLinePath(
      "/apps/commercial",
      "01",
      "102942",
      "01",
    );
    expect(href).toContain("/analytics/otd/01/102942/01");
    expect(otdLineLinkTitle("102942", "01")).toBe("Abrir linha OTD 102942/01");
  });
});
