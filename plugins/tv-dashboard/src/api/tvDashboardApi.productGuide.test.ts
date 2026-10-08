import { afterEach, describe, expect, it, vi } from "vitest";

import { HttpRequestError } from "./httpClient";
import { fetchProductGuideHelp } from "./tvDashboardApi";

function ok(data: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify({ success: true, data }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

function fail(status: number, body: unknown = { message: "err" }) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

const TOPIC = {
  id: "playlist",
  title: "Programações",
  summary: "Playlist de telas para TVs.",
  how_to_use: ["Agrupe telas."],
  related_topics: ["slide"],
};

describe("fetchProductGuideHelp", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("busca a projeção help-safe completa (sem body, sem dados de domínio)", async () => {
    const fetchMock = vi.fn(() =>
      ok({ schema: "product_guide_help_v1", registry_version: "1.0.0", topics: [TOPIC] }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const data = await fetchProductGuideHelp();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/apps/tv-dashboard-api/product-guides");
    expect(init.method).toBe("GET");
    expect(init).not.toHaveProperty("body");
    expect(data.schema).toBe("product_guide_help_v1");
    expect(data.registry_version).toBe("1.0.0");
    expect(data.topics).toHaveLength(1);
    expect(data.topics?.[0]?.id).toBe("playlist");
    // projeção help-safe: campos internos nunca trafegam
    expect(data.topics?.[0]).not.toHaveProperty("capability_refs");
    expect(data.topics?.[0]).not.toHaveProperty("operation_refs");
    expect(data.topics?.[0]).not.toHaveProperty("agent_guidance");
  });

  it("propaga AbortSignal", async () => {
    const fetchMock = vi.fn(() =>
      ok({ schema: "product_guide_help_v1", topics: [TOPIC] }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const controller = new AbortController();
    await fetchProductGuideHelp({ signal: controller.signal });
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.signal).toBe(controller.signal);
  });

  it.each([401, 403])("propaga HttpRequestError para auth (%i)", async (status) => {
    vi.stubGlobal("fetch", vi.fn(() => fail(status)));
    await expect(fetchProductGuideHelp()).rejects.toMatchObject({
      name: "HttpRequestError",
      status,
    });
  });

  it("propaga 404 como HttpRequestError (configuração/drift)", async () => {
    vi.stubGlobal("fetch", vi.fn(() => fail(404)));
    await expect(fetchProductGuideHelp()).rejects.toBeInstanceOf(HttpRequestError);
    await expect(fetchProductGuideHelp()).rejects.toMatchObject({ status: 404 });
  });

  it("propaga 5xx como HttpRequestError (indisponível)", async () => {
    vi.stubGlobal("fetch", vi.fn(() => fail(503, {})));
    await expect(fetchProductGuideHelp()).rejects.toMatchObject({ status: 503 });
  });

  it("propaga erro de rede", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))));
    await expect(fetchProductGuideHelp()).rejects.toBeInstanceOf(TypeError);
  });

  it("rejeita payload com schema inesperado", async () => {
    vi.stubGlobal("fetch", vi.fn(() => ok({ schema: "other_v9", topics: [] })));
    await expect(fetchProductGuideHelp()).rejects.toThrow(/inesperado/);
  });
});
