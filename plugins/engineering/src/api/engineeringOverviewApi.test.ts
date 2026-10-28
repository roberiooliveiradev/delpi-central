import { afterEach, describe, expect, it, vi } from "vitest";

import { getEngineeringOverview } from "./engineeringOverviewApi";
import type { OverviewIndicator } from "../types/overview";

const INDICATOR: OverviewIndicator = {
  id: "lmp_on_time",
  label: "% LMP dentro do prazo",
  family: "lmp",
  availability: "available",
  value: 92.5,
  unit: "%",
  scope: "consolidado",
  source: "api-delpi",
  source_endpoint: "GET /engineering/lmps/dashboard/summary",
};

function overviewPayload(overrides: Record<string, unknown> = {}) {
  return {
    success: true,
    message: null,
    data: {
      schema_version: "1.0",
      generated_at: "2026-10-28T12:00:00Z",
      status: "available",
      filters: {},
      indicators: [INDICATOR],
      ...overrides,
    },
    meta: { operationId: "get_engineering_overview" },
  };
}

function stubFetch(body: unknown, status = 200) {
  const spy = vi.fn(
    async () => new Response(JSON.stringify(body), { status }),
  );
  vi.stubGlobal("fetch", spy);
  return spy;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("getEngineeringOverview", () => {
  it("consome o envelope canônico e devolve data", async () => {
    stubFetch(overviewPayload());
    const overview = await getEngineeringOverview({});
    expect(overview.schema_version).toBe("1.0");
    expect(overview.indicators).toHaveLength(1);
    expect(overview.indicators[0].id).toBe("lmp_on_time");
  });

  it("serializa os filtros do contrato", async () => {
    const spy = stubFetch(overviewPayload());
    await getEngineeringOverview({
      start_date: "2026-10-01",
      end_date: "2026-10-31",
      competence: "2026-10",
      branch: "01",
    });
    const url = String(spy.mock.calls[0][0]);
    expect(url).toContain("/apps/engineering-api/v1/overview?");
    expect(url).toContain("start_date=2026-10-01");
    expect(url).toContain("end_date=2026-10-31");
    expect(url).toContain("competence=2026-10");
    expect(url).toContain("branch=01");
  });

  it("omite filtros ausentes da query", async () => {
    const spy = stubFetch(overviewPayload());
    await getEngineeringOverview({ branch: "02" });
    const url = String(spy.mock.calls[0][0]);
    expect(url).not.toContain("start_date");
    expect(url).not.toContain("competence");
    expect(url).toContain("branch=02");
  });

  it("rejeita envelope sem success", async () => {
    stubFetch({ success: false, message: "erro", data: null });
    await expect(getEngineeringOverview({})).rejects.toMatchObject({
      kind: "contract_error",
    });
  });

  it("rejeita indicador fora do contrato", async () => {
    stubFetch(
      overviewPayload({ indicators: [{ id: "x", family: "outra" }] }),
    );
    await expect(getEngineeringOverview({})).rejects.toMatchObject({
      kind: "contract_error",
    });
  });

  it("mapeia 401 para unauthorized", async () => {
    stubFetch({}, 401);
    await expect(getEngineeringOverview({})).rejects.toMatchObject({
      kind: "unauthorized",
    });
  });

  it("mapeia 403 para forbidden", async () => {
    stubFetch({}, 403);
    await expect(getEngineeringOverview({})).rejects.toMatchObject({
      kind: "forbidden",
    });
  });
});
