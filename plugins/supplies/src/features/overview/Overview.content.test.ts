import { describe, expect, it } from "vitest";

import { canAccessView } from "../../app/routeAccess";
import {
  firstDayOfMonthIso,
  OVERVIEW_CONTENT,
  temporalNatureLabel,
  todayIso,
} from "./overviewContent";

describe("Overview content", () => {
  it("exposes temporal nature labels for all KPI natures", () => {
    expect(temporalNatureLabel("interval")).toBe("Intervalo");
    expect(temporalNatureLabel("snapshot")).toBe("Snapshot");
    expect(temporalNatureLabel("state")).toBe("Estado atual");
    expect(OVERVIEW_CONTENT.title).toBe("Visão geral");
    expect(OVERVIEW_CONTENT.description).toMatch(/Início/i);
  });

  it("defaults period to first day of month through today", () => {
    const fixed = new Date(2026, 8, 8);
    expect(firstDayOfMonthIso(fixed)).toBe("2026-09-01");
    expect(todayIso(fixed)).toBe("2026-09-08");
  });

  it("requires analytics capability for overview view", () => {
    expect(
      canAccessView("overview", {
        portal: true,
        purchaseRequests: false,
        operations: false,
        analytics: false,
        administration: false,
        viewAll: false,
        export: false,
      }),
    ).toBe(false);
    expect(
      canAccessView("overview", {
        portal: true,
        purchaseRequests: false,
        operations: false,
        analytics: true,
        administration: false,
        viewAll: false,
        export: false,
      }),
    ).toBe(true);
  });
});
