import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createNonconformity,
  deleteNonconformity,
  fetchNcIndicators,
  fetchNonconformities,
  fetchNonconformitiesExport,
  fetchNonconformity,
  fetchNonconformityContext,
  fetchNonconformityHistory,
  fetchProblemTags,
  importNonconformities,
  updateNonconformity,
} from "./nonconformityApi";

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

const BASE = "/apps/engineering-api/v1/nonconformities";
const RECORD_ID = "2f0e2d62-9f4d-4f0d-9f2a-2f4d8f1c8a01";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("E-NC-01 — GET /v1/nonconformities", () => {
  it("serializa filtros, sort e paginação sem barra final", async () => {
    const spy = stubFetch(
      okEnvelope({ items: [], total: 0, page: 1, page_size: 20 }),
    );
    await fetchNonconformities({
      status: "open",
      sale_number: "004101",
      lmp_number: "LMP-7",
      customer_name: "Cliente",
      product_code: "ABC-1",
      problem_tag: "Medição incorreta",
      date_start: "2026-01-01",
      date_end: "2026-01-31",
      sort_by: "occurrence_date",
      sort_dir: "desc",
      page: 2,
      page_size: 20,
    });
    const url = String(spy.mock.calls[0]?.[0]);
    expect(url.startsWith(`${BASE}?`)).toBe(true);
    expect(url).toContain("status=open");
    expect(url).toContain("sale_number=004101");
    expect(url).toContain("problem_tag=Medi%C3%A7%C3%A3o+incorreta");
    expect(url).toContain("sort_by=occurrence_date");
    expect(url).toContain("sort_dir=desc");
    expect(url).toContain("page=2");
    expect(url).toContain("page_size=20");
  });

  it("omite filtros vazios e indefinidos", async () => {
    const spy = stubFetch(
      okEnvelope({ items: [], total: 0, page: 1, page_size: 20 }),
    );
    await fetchNonconformities({ status: "", page: 1 });
    const url = String(spy.mock.calls[0]?.[0]);
    expect(url).toBe(`${BASE}?page=1`);
  });
});

describe("E-NC-02..05 — detalhe, histórico, indicadores e tags", () => {
  it("detalhe usa o id no path", async () => {
    const spy = stubFetch(okEnvelope({ id: RECORD_ID }));
    await fetchNonconformity(RECORD_ID);
    expect(String(spy.mock.calls[0]?.[0])).toBe(`${BASE}/${RECORD_ID}`);
  });

  it("histórico desembrulha items", async () => {
    stubFetch(okEnvelope({ items: [{ id: 1, event_type: "created" }] }));
    const items = await fetchNonconformityHistory(RECORD_ID);
    expect(items).toHaveLength(1);
    expect(items[0]?.event_type).toBe("created");
  });

  it("indicadores usam rota dedicada", async () => {
    const spy = stubFetch(
      okEnvelope({
        current_days_without_nc: 12,
        record_days_without_nc: 30,
        last_nc_date: "2026-01-10",
        nc_count: 4,
      }),
    );
    const data = await fetchNcIndicators();
    expect(String(spy.mock.calls[0]?.[0])).toBe(`${BASE}/indicators`);
    expect(data.current_days_without_nc).toBe(12);
  });

  it("tags desembrulham items do catálogo", async () => {
    stubFetch(okEnvelope({ items: [{ id: 3, label: "Atraso" }] }));
    const tags = await fetchProblemTags();
    expect(tags[0]?.label).toBe("Atraso");
  });

  it("contexto usa rota dedicada do registro", async () => {
    const spy = stubFetch(
      okEnvelope({ ov_status: "not_linked", product_contexts: [] }),
    );
    await fetchNonconformityContext(RECORD_ID);
    expect(String(spy.mock.calls[0]?.[0])).toBe(
      `${BASE}/${RECORD_ID}/context`,
    );
  });
});

describe("E-NC-06 — exportação", () => {
  it("retorna payload de exportação versionado", async () => {
    stubFetch(
      okEnvelope({ version: 1, generated_at: "2026-10-29T00:00:00Z", count: 2, items: [] }),
    );
    const payload = await fetchNonconformitiesExport();
    expect(payload.version).toBe(1);
  });
});

describe("E-NC-07..10 — mutações", () => {
  it("create envia POST no recurso base", async () => {
    const spy = stubFetch(okEnvelope({ id: RECORD_ID }), 201);
    await createNonconformity({ status: "open" });
    const [url, init] = spy.mock.calls[0] ?? [];
    expect(String(url)).toBe(BASE);
    expect((init as RequestInit).method).toBe("POST");
  });

  it("update envia PUT com expected_updated_at", async () => {
    const spy = stubFetch(okEnvelope({ id: RECORD_ID }));
    await updateNonconformity(RECORD_ID, {
      status: "done",
      expected_updated_at: "2026-10-01T10:00:00Z",
    });
    const [url, init] = spy.mock.calls[0] ?? [];
    expect(String(url)).toBe(`${BASE}/${RECORD_ID}`);
    expect((init as RequestInit).method).toBe("PUT");
    const body = JSON.parse(String((init as RequestInit).body));
    expect(body.expected_updated_at).toBe("2026-10-01T10:00:00Z");
  });

  it("delete envia DELETE no registro", async () => {
    const spy = stubFetch(
      okEnvelope({ id: RECORD_ID, deleted: true }),
    );
    await deleteNonconformity(RECORD_ID);
    const [url, init] = spy.mock.calls[0] ?? [];
    expect(String(url)).toBe(`${BASE}/${RECORD_ID}`);
    expect((init as RequestInit).method).toBe("DELETE");
  });

  it("import envia dry_run e confirm_replace explícitos", async () => {
    const spy = stubFetch(
      okEnvelope({
        created: 0,
        deleted: 0,
        skipped: 1,
        errors: 0,
        items: [],
      }),
    );
    await importNonconformities([{ status: "open" }], {
      dryRun: true,
      confirmReplace: true,
    });
    const [url, init] = spy.mock.calls[0] ?? [];
    expect(String(url)).toBe(`${BASE}/import`);
    const body = JSON.parse(String((init as RequestInit).body));
    expect(body.dry_run).toBe(true);
    expect(body.confirm_replace).toBe(true);
  });
});

describe("estados honestos — erros classificados pelo httpClient", () => {
  it("404 propaga status para a camada de UI", async () => {
    stubFetch({ success: false, message: "not found" }, 404);
    await expect(fetchNonconformity(RECORD_ID)).rejects.toMatchObject({
      status: 404,
    });
  });

  it("403 propaga acesso negado sem mascaramento", async () => {
    stubFetch({ success: false, message: "forbidden" }, 403);
    await expect(fetchNonconformities({})).rejects.toMatchObject({
      status: 403,
    });
  });
});
