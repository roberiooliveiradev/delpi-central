import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getLmpsDashboard,
  getLmpsDashboardItems,
  getLmpBySaleNumber,
  getLmpHistoryEvents,
  getLmpHistoryFlow,
  getLmpGoalContext,
  listLmps,
} from "./lmpApi";
import { fetchLmpNonconformityStreak } from "./lmpNonconformityApi";
import { fetchDepartmentIdd } from "./departmentIddApi";
import { getProductStructure } from "./productApi";

function stubFetch(body: unknown, status = 200) {
  const spy = vi.fn<typeof fetch>(
    async () => new Response(JSON.stringify(body), { status }),
  );
  vi.stubGlobal("fetch", spy);
  return spy;
}

function okEnvelope<T>(data: T) {
  return { success: true, message: null, data, meta: null };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("E-LMP-01 — GET /v1/lmps (contrato consolidado)", () => {
  it("lista serializa filtros ISO sem barra final no path", async () => {
    const spy = stubFetch(okEnvelope({ items: [], total: 0, page: 1, page_size: 50 }));
    await getLmpsDashboard({
      start_date: "20261001",
      end_date: "2026-10-31",
      branch: "01",
      listing_type: "LMP",
      status: "Atrasado",
      page: 2,
      page_size: 100,
    });
    const url = String(spy.mock.calls[0]?.[0]);
    expect(url).toContain("/apps/engineering-api/v1/lmps?");
    expect(url).not.toContain("/lmps/?");
    expect(url).toContain("start_date=2026-10-01");
    expect(url).toContain("end_date=2026-10-31");
    expect(url).toContain("branch=01");
    expect(url).toContain("listing_type=LMP");
    expect(url).toContain("status=Atrasado");
    expect(url).toContain("page=2");
    expect(url).toContain("page_size=100");
  });

  it("omite valores 'Todos' e parâmetros vazios", async () => {
    const spy = stubFetch(okEnvelope({ items: [], total: 0 }));
    await getLmpsDashboard({ listing_type: "Todos", status: "Todos" });
    const url = String(spy.mock.calls[0]?.[0]);
    expect(url).toBe("/apps/engineering-api/v1/lmps");
  });

  it("dashboard consolida items+summary+charts num único payload", async () => {
    const payload = {
      items: [{ sale_number: "003696" }],
      total: 1,
      page: 1,
      page_size: 50,
      summary: { total_lmps: 1, percent_dentro_prazo: 100, avg_lead_time: 3 },
      charts: { levelData: [{ name: "Nível 1", value: 1 }] },
    };
    const spy = stubFetch(okEnvelope(payload));
    const data = await getLmpsDashboard({ branch: "01" });
    expect(String(spy.mock.calls[0]?.[0])).toContain(
      "/apps/engineering-api/v1/lmps?branch=01",
    );
    expect(data.summary?.total_lmps).toBe(1);
    expect(data.charts?.levelData?.[0]?.value).toBe(1);
    expect(data.items).toHaveLength(1);
  });

  it("getLmpsDashboardItems usa o mesmo contrato consolidado", async () => {
    const spy = stubFetch(
      okEnvelope({ items: [], total: 0, page: 1, page_size: 50 }),
    );
    await getLmpsDashboardItems({});
    expect(String(spy.mock.calls[0]?.[0])).toBe(
      "/apps/engineering-api/v1/lmps",
    );
  });
});

describe("E-LMP-02/04/05 — detalhe e histórico", () => {
  it("detalhe codifica o número da proposta e envia filtros", async () => {
    const spy = stubFetch(okEnvelope({ item: { sale_number: "003696" } }));
    await getLmpBySaleNumber("003696", { branch: "01", revision: "2" });
    const url = String(spy.mock.calls[0]?.[0]);
    expect(url).toContain("/apps/engineering-api/v1/lmps/003696?");
    expect(url).toContain("branch=01");
    expect(url).toContain("revision=2");
  });

  it("eventos e fluxo usam as rotas de histórico dedicadas", async () => {
    const spy = stubFetch(okEnvelope({ items: [], total: 0 }));
    await getLmpHistoryEvents("003696");
    expect(String(spy.mock.calls[0]?.[0])).toBe(
      "/apps/engineering-api/v1/lmps/003696/history/events",
    );
    await getLmpHistoryFlow("003696", { branch: "01" });
    expect(String(spy.mock.calls[1]?.[0])).toBe(
      "/apps/engineering-api/v1/lmps/003696/history/flow?branch=01",
    );
  });

  it("fonte indisponível propage erro honesto (nunca lista vazia)", async () => {
    stubFetch(okEnvelope({ status: "unavailable", reason: "timeout" }));
    await expect(getLmpBySaleNumber("003696")).rejects.toThrow(
      /indisponível/i,
    );
  });
});

describe("Adapters delegados — metas, IDD, streak, estrutura", () => {
  it("goal-context bate na rota governada e retorna null fora de available", async () => {
    stubFetch(okEnvelope({ status: "unavailable" }));
    const goal = await getLmpGoalContext({ branch: "01" });
    expect(goal).toBeNull();

    const spy = stubFetch(
      okEnvelope({ status: "available", data: { goal_value: 90 } }),
    );
    const data = await getLmpGoalContext();
    expect(data).toEqual({ goal_value: 90 });
    expect(String(spy.mock.calls[0]?.[0])).toBe(
      "/apps/engineering-api/v1/lmps/goal-context",
    );
  });

  it("streak de NC usa a rota governada read-only", async () => {
    const spy = stubFetch(
      okEnvelope({ status: "available", data: { days_without_nc: 12 } }),
    );
    const streak = await fetchLmpNonconformityStreak();
    expect(streak).toEqual({ days_without_nc: 12 });
    expect(String(spy.mock.calls[0]?.[0])).toBe(
      "/apps/engineering-api/v1/lmps/nonconformities/streak",
    );
  });

  it("IDD departamental envia department_id e período", async () => {
    const spy = stubFetch(
      okEnvelope({ status: "available", data: { item: { score: 8.4 } } }),
    );
    const item = await fetchDepartmentIdd({
      departmentId: "engineering",
      competence: "2026-10",
      startDate: "2026-10-01",
      endDate: "2026-10-31",
      branch: "01",
    });
    const url = String(spy.mock.calls[0]?.[0]);
    expect(url).toContain("/apps/engineering-api/v1/lmps/department-idd?");
    expect(url).toContain("department_id=engineering");
    expect(url).toContain("competence=2026-10");
    expect(item).toEqual({ score: 8.4 });
  });

  it("IDD forbidden vira erro explícito do owner", async () => {
    stubFetch(okEnvelope({ status: "forbidden" }));
    await expect(
      fetchDepartmentIdd({ departmentId: "engineering" }),
    ).rejects.toThrow(/Strategic Indicators/i);
  });

  it("estrutura de produto usa rota governada com code encodado", async () => {
    const spy = stubFetch(
      okEnvelope({ status: "available", data: { product_code: "X 1/2" } }),
    );
    const data = await getProductStructure("X 1/2");
    expect(String(spy.mock.calls[0]?.[0])).toBe(
      "/apps/engineering-api/v1/products/X%201%2F2/structure?max_depth=6&page_size=200",
    );
    expect(data).toEqual({ product_code: "X 1/2" });
  });

  it("estrutura forbidden propaga estado honesto", async () => {
    stubFetch(okEnvelope({ status: "forbidden" }));
    await expect(getProductStructure("ABC")).rejects.toThrow(/indisponível/i);
  });
});

describe("Resiliência do cliente canônico", () => {
  it("401 propaga HomeApiError 'unauthorized' (fail-closed)", async () => {
    stubFetch({}, 401);
    await expect(listLmps({})).rejects.toMatchObject({
      kind: "unauthorized",
      status: 401,
    });
  });

  it("403 propaga HomeApiError 'forbidden'", async () => {
    stubFetch({}, 403);
    await expect(listLmps({})).rejects.toMatchObject({
      kind: "forbidden",
      status: 403,
    });
  });
});
