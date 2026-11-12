import { describe, expect, it } from "vitest";

import {
  detectNonMovingWindowPreset,
  getNonMovingWindowDates,
} from "./nonMovingWindowPresets";

describe("GLPI #1197 — atalhos da janela de consumo", () => {
  const reference = new Date(2026, 10, 12, 12, 0, 0);

  it("uses 6 and 12 rolling months (not the first day of month)", () => {
    expect(getNonMovingWindowDates("last_6_months", reference)).toEqual({
      dateStart: "2026-05-12",
      dateEnd: "2026-11-12",
    });
    expect(getNonMovingWindowDates("last_12_months", reference)).toEqual({
      dateStart: "2025-11-12",
      dateEnd: "2026-11-12",
    });
  });

  it("recognizes both presets after URL or session restoration", () => {
    const six = getNonMovingWindowDates("last_6_months", reference);
    const twelve = getNonMovingWindowDates("last_12_months", reference);
    expect(detectNonMovingWindowPreset(six.dateStart, six.dateEnd, reference))
      .toBe("last_6_months");
    expect(detectNonMovingWindowPreset(twelve.dateStart, twelve.dateEnd, reference))
      .toBe("last_12_months");
  });

  it("detects manual or past-month periods as custom", () => {
    expect(detectNonMovingWindowPreset("2026-09-01", "2026-09-30", reference))
      .toBe("custom");
    expect(detectNonMovingWindowPreset("2026-01-01", "2026-11-12", reference))
      .toBe("custom");
    expect(detectNonMovingWindowPreset("2025-11-12", "2026-11-11", reference))
      .toBe("custom");
  });

  it("clamps month ends and leap days consistently with the existing date helper", () => {
    expect(getNonMovingWindowDates("last_6_months", new Date(2026, 7, 31, 12)))
      .toEqual({ dateStart: "2026-02-28", dateEnd: "2026-08-31" });
    expect(getNonMovingWindowDates("last_12_months", new Date(2028, 1, 29, 12)))
      .toEqual({ dateStart: "2027-02-28", dateEnd: "2028-02-29" });
  });
});
