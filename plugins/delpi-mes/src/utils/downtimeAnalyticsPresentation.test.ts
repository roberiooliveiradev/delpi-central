import { describe, expect, it } from "vitest";

import type { DowntimesRouteParams } from "../hooks/useDelpiMesRoute";
import {
  PENDING_REASON_GROUP_KEY,
  buildDowntimeAnalyticsQuery,
  buildHeatmapRows,
  dayKeyLabel,
  daySeriesPoints,
} from "./downtimeAnalyticsPresentation";

const PARAMS: DowntimesRouteParams = {
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

describe("buildDowntimeAnalyticsQuery", () => {
  const now = new Date("2026-02-11T15:00:00.000Z"); // qua 12:00 SP

  it("usa o mesmo universo da listagem, sem page/sort/downtimeId", () => {
    const query = buildDowntimeAnalyticsQuery("01", {
      ...PARAMS,
      workCenter: " CT-35 ",
      reasonCode: "SETUP",
      source: "system",
      classification: "pending",
      sort: "oldest",
      downtimeId: "abc",
      page: 4,
      pageSize: 100,
    }, now);
    expect(query).toEqual({
      branch: "01",
      from: "2026-02-05T03:00:00.000Z", // 7d: início de 05/02 em SP
      to: undefined,
      workCenter: "CT-35",
      reasonCode: "SETUP",
      source: "system",
      classification: "pending",
    });
    expect(query).not.toHaveProperty("page");
    expect(query).not.toHaveProperty("sort");
    expect(query).not.toHaveProperty("downtimeId");
  });

  it("retorna null quando o período customizado não tem início", () => {
    const query = buildDowntimeAnalyticsQuery("01", {
      ...PARAMS,
      period: "custom",
      to: "2026-02-10",
    }, now);
    expect(query).toBeNull();
  });

  it("período customizado cobre o dia final inteiro (limite exclusivo)", () => {
    const query = buildDowntimeAnalyticsQuery("01", {
      ...PARAMS,
      period: "custom",
      from: "2026-02-09",
      to: "2026-02-10",
    }, now);
    expect(query?.from).toBe("2026-02-09T03:00:00.000Z");
    expect(query?.to).toBe("2026-02-11T03:00:00.000Z");
  });
});

describe("buildHeatmapRows", () => {
  it("monta 7 linhas seg→dom com 24 colunas, zeros nas ausências", () => {
    const { rows, maxSeconds } = buildHeatmapRows([
      { weekday: 0, weekdayLabel: "seg", hour: 10, seconds: 3600, occurrencesCount: 2 },
      { weekday: 6, weekdayLabel: "dom", hour: 23, seconds: 600, occurrencesCount: 1 },
    ]);
    expect(rows).toHaveLength(7);
    expect(rows[0].weekdayLabel).toBe("Seg");
    expect(rows[6].weekdayLabel).toBe("Dom");
    expect(rows[0].hours).toHaveLength(24);
    expect(rows[0].hours[10]).toEqual({ hour: 10, seconds: 3600, occurrencesCount: 2 });
    expect(rows[0].hours[0].seconds).toBe(0);
    expect(rows[6].hours[23].seconds).toBe(600);
    expect(maxSeconds).toBe(3600);
  });

  it("matriz vazia produz zeros seguros", () => {
    const { rows, maxSeconds } = buildHeatmapRows([]);
    expect(rows).toHaveLength(7);
    expect(maxSeconds).toBe(0);
    expect(rows.every((row) => row.hours.every((h) => h.seconds === 0))).toBe(true);
  });
});

describe("daySeriesPoints / dayKeyLabel", () => {
  const days = [
    { date: "2026-02-09", weekday: 0, seconds: 3660, occurrencesCount: 1 },
    { date: "2026-02-10", weekday: 1, seconds: 0, occurrencesCount: 0 },
  ];

  it("rotula dd/mm a partir da chave civil SP e usa minutos", () => {
    const points = daySeriesPoints(days, "seconds");
    expect(points).toEqual([
      { label: "09/02", value: 61 },
      { label: "10/02", value: 0 },
    ]);
  });

  it("métrica de ocorrências usa contagens do dia", () => {
    expect(daySeriesPoints(days, "occurrences")[0].value).toBe(1);
  });

  it("dayKeyLabel é estável", () => {
    expect(dayKeyLabel("2026-02-09")).toBe("09/02");
  });

  it("a chave do grupo pendente é estável para o drill-down", () => {
    expect(PENDING_REASON_GROUP_KEY).toBe("pending");
  });
});
