import { afterEach, describe, expect, it, vi } from "vitest";

import {
  fetchProductFilterOptions,
  fetchProductParents,
  fetchProductStructure,
  fetchProductSuppliers,
  searchProducts,
} from "./productApi";

function stubFetch(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(body), { status })),
  );
}

function envelope(data: unknown) {
  return { success: true, message: null, data };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("productApi — normalização de envelopes (GATE A)", () => {
  it("structure: desempacota o envelope delegado {status,data}", async () => {
    stubFetch(
      envelope({
        status: "available",
        data: { root: null, items: [], total: 0 },
      }),
    );
    const result = await fetchProductStructure("30190123");
    expect(result.items).toEqual([]);
    expect(result.total).toBe(0);
  });

  it("structure: aceita também o payload plano (sibling)", async () => {
    stubFetch(envelope({ root: null, items: [{ code: "X" }], total: 1 }));
    const result = await fetchProductStructure("30190123");
    expect(result.items).toHaveLength(1);
  });

  it("structure: status forbidden vira HomeApiError honesto", async () => {
    stubFetch(
      envelope({ status: "forbidden", data: null }),
    );
    await expect(fetchProductStructure("30190123")).rejects.toMatchObject({
      kind: "forbidden",
      status: 403,
    });
  });

  it("structure: status indisponível vira unavailable 502", async () => {
    stubFetch(envelope({ status: "unavailable", data: null }));
    await expect(fetchProductStructure("30190123")).rejects.toMatchObject({
      kind: "unavailable",
      status: 502,
    });
  });

  it("structure: payload inválido (items ausente) vira contract_error", async () => {
    stubFetch(envelope({ status: "available", data: { root: null } }));
    await expect(fetchProductStructure("30190123")).rejects.toMatchObject({
      kind: "contract_error",
    });
  });

  it("parents/suppliers/search: items ausente vira contract_error", async () => {
    stubFetch(envelope({ total: 0 }));
    await expect(fetchProductParents("X")).rejects.toMatchObject({
      kind: "contract_error",
    });
    stubFetch(envelope({ total: 0 }));
    await expect(fetchProductSuppliers("X")).rejects.toMatchObject({
      kind: "contract_error",
    });
    stubFetch(envelope({ total: 0 }));
    await expect(searchProducts({})).rejects.toMatchObject({
      kind: "contract_error",
    });
  });
});

describe("productApi — filter-options", () => {
  it("mapeia grupos e tipos oficiais", async () => {
    stubFetch(
      envelope({ groups: ["3019", "3020"], types: ["MP", "PA"] }),
    );
    const options = await fetchProductFilterOptions();
    expect(options.groups).toEqual(["3019", "3020"]);
    expect(options.types).toEqual(["MP", "PA"]);
  });

  it("tolera payload parcial sem quebrar", async () => {
    stubFetch(envelope({}));
    const options = await fetchProductFilterOptions();
    expect(options).toEqual({ groups: [], types: [] });
  });
});
