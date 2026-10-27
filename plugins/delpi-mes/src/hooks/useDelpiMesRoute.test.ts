import { describe, expect, it } from "vitest";

import {
  buildDelpiMesHref,
  buildDowntimesHref,
  buildRegistrationHref,
  parseDelpiMesRoute,
  type DowntimesRouteParams,
} from "./useDelpiMesRoute";

const DEFAULT_DOWNTIMES: DowntimesRouteParams = {
  period: "7d",
  from: null,
  to: null,
  workCenter: null,
  reasonCode: null,
  source: null,
  classification: null,
  status: null,
  sort: "recent",
  downtimeId: null,
  page: 1,
  pageSize: 50,
};

const base = { branch: "01" as const, workCenter: null, registrationPage: null, areaExplicit: false };

describe("Delpi MES routing", () => {
  it("defaults the product root to monitoring and branch 01", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes", "")).toEqual({
      area: "monitoring",
      ...base,
      downtimes: DEFAULT_DOWNTIMES,
    });
  });

  it("preserves area and branch in a shareable URL", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/downtimes", "?branch=02")).toEqual({
      area: "downtimes",
      ...base,
      areaExplicit: true,
      branch: "02",
      downtimes: DEFAULT_DOWNTIMES,
    });
    expect(buildDelpiMesHref("history", "02")).toBe("/apps/delpi-mes/history?branch=02");
  });

  it("parses the selected work center only on monitoring", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/monitoring", "?branch=01&workCenter=CT-35")).toEqual({
      area: "monitoring",
      ...base,
      areaExplicit: true,
      workCenter: "CT-35",
      downtimes: DEFAULT_DOWNTIMES,
    });
    expect(
      parseDelpiMesRoute("/apps/delpi-mes/downtimes", "?branch=01&workCenter=CT-35").workCenter,
    ).toBeNull();
    expect(buildDelpiMesHref("monitoring", "01", "CT 35")).toBe(
      "/apps/delpi-mes/monitoring?branch=01&workCenter=CT%2035",
    );
  });

  it("routes the registrations hub without branch", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/registrations", "")).toEqual({
      area: "registrations",
      ...base,
      areaExplicit: true,
      downtimes: DEFAULT_DOWNTIMES,
    });
    expect(buildDelpiMesHref("registrations", "02")).toBe("/apps/delpi-mes/registrations");
  });

  it("routes the downtime-reasons catalog page", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes/registrations/downtime-reasons", "")).toEqual({
      area: "registrations",
      ...base,
      areaExplicit: true,
      registrationPage: "downtime-reasons",
      downtimes: DEFAULT_DOWNTIMES,
    });
    expect(buildRegistrationHref("downtime-reasons")).toBe(
      "/apps/delpi-mes/registrations/downtime-reasons",
    );
  });

  it("marks areaExplicit only when the URL names a known area", () => {
    expect(parseDelpiMesRoute("/apps/delpi-mes", "").areaExplicit).toBe(false);
    expect(parseDelpiMesRoute("/apps/delpi-mes/", "").areaExplicit).toBe(false);
    expect(parseDelpiMesRoute("/apps/delpi-mes/downtimes", "").areaExplicit).toBe(true);
    expect(parseDelpiMesRoute("/apps/delpi-mes/history", "").areaExplicit).toBe(true);
    // Segmento desconhecido nao e area explicita — cai no fallback da rota inicial
    expect(parseDelpiMesRoute("/apps/delpi-mes/unknown", "").areaExplicit).toBe(false);
    expect(parseDelpiMesRoute("/apps/delpi-mes/unknown", "").area).toBe("monitoring");
  });

  it("ignores branch and unknown segments on registrations routes", () => {
    expect(
      parseDelpiMesRoute("/apps/delpi-mes/registrations", "?branch=02").registrationPage,
    ).toBeNull();
    expect(
      parseDelpiMesRoute("/apps/delpi-mes/registrations/other", "").registrationPage,
    ).toBeNull();
    expect(parseDelpiMesRoute("/apps/delpi-mes/registrations", "").workCenter).toBeNull();
  });
});

describe("Delpi MES routing — downtimes area", () => {
  it("parses filters, pagination and selection from the URL", () => {
    const parsed = parseDelpiMesRoute(
      "/apps/delpi-mes/downtimes",
      "?branch=02&period=30d&workCenter=CT-35&reasonCode=SETUP&source=system" +
        "&classification=confirmed&status=open&sort=oldest&page=3&pageSize=100&downtimeId=42",
    );
    expect(parsed.area).toBe("downtimes");
    expect(parsed.branch).toBe("02");
    expect(parsed.downtimes).toEqual({
      period: "30d",
      from: null,
      to: null,
      workCenter: "CT-35",
      reasonCode: "SETUP",
      source: "system",
      classification: "confirmed",
      status: "open",
      sort: "oldest",
      downtimeId: "42",
      page: 3,
      pageSize: 100,
    });
  });

  it("sanitizes invalid values back to defaults", () => {
    const parsed = parseDelpiMesRoute(
      "/apps/delpi-mes/downtimes",
      "?period=bogus&classification=bogus&sort=bogus&page=-2&pageSize=999&from=not-a-day",
    );
    expect(parsed.downtimes.period).toBe("7d");
    expect(parsed.downtimes.classification).toBeNull();
    expect(parsed.downtimes.sort).toBe("recent");
    expect(parsed.downtimes.page).toBe(1);
    expect(parsed.downtimes.pageSize).toBe(50);
    expect(parsed.downtimes.from).toBeNull();
  });

  it("keeps the custom period and valid day keys", () => {
    const parsed = parseDelpiMesRoute(
      "/apps/delpi-mes/downtimes",
      "?period=custom&from=2026-02-01&to=2026-02-10",
    );
    expect(parsed.downtimes.period).toBe("custom");
    expect(parsed.downtimes.from).toBe("2026-02-01");
    expect(parsed.downtimes.to).toBe("2026-02-10");
  });

  it("serializes only non-default downtimes params", () => {
    const href = buildDowntimesHref("01", {
      ...DEFAULT_DOWNTIMES,
      reasonCode: "MATERIAL",
      page: 2,
      downtimeId: "7",
    });
    expect(href).toBe("/apps/delpi-mes/downtimes?branch=01&reasonCode=MATERIAL&downtimeId=7&page=2");
    expect(buildDowntimesHref("02", DEFAULT_DOWNTIMES)).toBe(
      "/apps/delpi-mes/downtimes?branch=02",
    );
  });

  it("round-trips the canonical href (parse(build(x)) === x)", () => {
    const filters: DowntimesRouteParams = {
      ...DEFAULT_DOWNTIMES,
      period: "custom",
      from: "2026-02-01",
      to: "2026-02-10",
      workCenter: "CT-35",
      classification: "pending",
      sort: "oldest",
      page: 2,
      pageSize: 100,
      downtimeId: "11",
    };
    const href = buildDowntimesHref("02", filters);
    const [path, search] = href.split("?");
    expect(parseDelpiMesRoute(path, "?" + search).downtimes).toEqual(filters);
    expect(parseDelpiMesRoute(path, "?" + search).branch).toBe("02");
  });

  it("never parses downtimes params outside the downtimes area", () => {
    expect(
      parseDelpiMesRoute("/apps/delpi-mes/history", "?branch=01&reasonCode=SETUP&page=4").downtimes,
    ).toEqual(DEFAULT_DOWNTIMES);
  });
});
