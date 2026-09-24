/**
 * E5 / CI-friendly paint-only contract gate.
 *
 * When enrich sets `serverDisplayApplied` / `display*`, slide paint must prefer
 * those strings (`preferServerTextDisplayRuns`) and must not re-run
 * `formatDisplayValue` on the TV path. See ADR
 * `tv-dashboard-api/docs/architecture/adr-tv-display-format-ownership.md`.
 */
import { describe, expect, it } from "vitest";

import {
  hasServerDisplayPaint,
  preferServerDisplayRunText,
  preferServerTextDisplayRuns,
} from "./serverDisplayPaint";

describe("serverDisplayPaint (paint-only contract)", () => {
  it("hasServerDisplayPaint detects serverDisplayApplied and display*", () => {
    expect(hasServerDisplayPaint({ serverDisplayApplied: true })).toBe(true);
    expect(hasServerDisplayPaint({ displayText: "42%" })).toBe(true);
    expect(
      hasServerDisplayPaint({
        displayRuns: [{ text: "01/01/2026" }],
      }),
    ).toBe(true);
    expect(hasServerDisplayPaint({ kpi: { value: 1 } })).toBe(false);
  });

  it("preferServerTextDisplayRuns wins over client reformat inputs", () => {
    const runs = preferServerTextDisplayRuns({
      serverDisplayApplied: true,
      displayRuns: [
        { text: "ACUMULADO " },
        { text: "03/08/2026", dataRef: { field: "filter.start_date", format: "raw" } },
      ],
      displayText: "ACUMULADO 03/08/2026",
      contextValues: { "filter.start_date": "2026-08-03" },
    });
    expect(runs).not.toBeNull();
    expect(runs!.map((r) => r.text).join("")).toBe("ACUMULADO 03/08/2026");
    expect(runs!.some((r) => r.text.includes("2026-08-03"))).toBe(false);
  });

  it("preferServerTextDisplayRuns falls back to displayText", () => {
    expect(
      preferServerTextDisplayRuns({
        serverDisplayApplied: true,
        displayText: "SERVER-ONLY",
      }),
    ).toEqual([{ text: "SERVER-ONLY" }]);
  });

  it("preferServerDisplayRunText matches field on displayRuns", () => {
    expect(
      preferServerDisplayRunText(
        {
          displayRuns: [
            { text: "03/08/2026", dataRef: { field: "filter.start_date" } },
          ],
        },
        "filter.start_date",
      ),
    ).toBe("03/08/2026");
    expect(
      preferServerDisplayRunText(
        { displayRuns: [{ text: "x", dataRef: { field: "other" } }] },
        "filter.start_date",
      ),
    ).toBeUndefined();
  });
});
