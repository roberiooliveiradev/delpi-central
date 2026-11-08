/** PRC catalogs — máquina de estados, mapeamento de opções e
 * proteção contra requests obsoletas (contrato D7). */

import { describe, expect, it, vi } from "vitest";

import type { Envelope, PrcCatalogItem } from "./api/productRegistrationApi";
import {
  catalogOptions,
  enumOptions,
  PRC_CATALOG_KINDS,
  PRC_CATALOG_PAGE_LIMIT,
  PrcCatalogStore,
  withSelectedOption,
} from "./prcCatalogs";

type CatalogPayload = { items: PrcCatalogItem[]; hasMore: boolean };
type FetchCatalog = (
  catalog: string,
  query?: string,
  signal?: AbortSignal,
  limit?: number,
) => Promise<Envelope<CatalogPayload>>;

const item = (code: string, label = ""): PrcCatalogItem => ({
  code,
  label,
  disabled: 0,
});

function deferred<T>() {
  let resolve!: (v: T) => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function storeWith(fetchCatalog: FetchCatalog) {
  return new PrcCatalogStore(fetchCatalog);
}

describe("PRC_CATALOG_KINDS", () => {
  it("mapeia os 4 catálogos TOTVS da ficha técnica", () => {
    expect(PRC_CATALOG_KINDS).toEqual({
      group: "product-groups",
      unit: "units",
      defaultWarehouse: "warehouses",
      accountingAccount: "accounting-accounts",
    });
  });
});

describe("catalogOptions", () => {
  it("monta label `code — description` e preserva zeros à esquerda", () => {
    const options = catalogOptions([
      item("01", "Almoxarifado"),
      item("0001", "Plástico"),
    ]);
    expect(options).toEqual([
      { value: "01", label: "01 — Almoxarifado" },
      { value: "0001", label: "0001 — Plástico" },
    ]);
    expect(options[0].value).toBe("01");
  });

  it("cai no código puro quando a descrição vem vazia", () => {
    expect(catalogOptions([item("UN", "  ")])).toEqual([
      { value: "UN", label: "UN" },
    ]);
  });

  it("ignora itens malformados sem quebrar a lista", () => {
    expect(
      catalogOptions([
        item("KG", "Quilo"),
        { code: null } as unknown as PrcCatalogItem,
        undefined as unknown as PrcCatalogItem,
      ]),
    ).toEqual([{ value: "KG", label: "KG — Quilo" }]);
  });
});

describe("enumOptions", () => {
  it("rotula o enum oficial de tipo de produto", () => {
    expect(enumOptions("productKind", ["MP", "PA", "PI"])).toEqual([
      { value: "MP", label: "MP — Matéria-prima" },
      { value: "PA", label: "PA — Produto acabado" },
      { value: "PI", label: "PI — Produto intermediário" },
    ]);
  });

  it("rotula produto de terceiros 1/2 como Não/Sim", () => {
    expect(enumOptions("thirdPartyProduct", ["1", "2"])).toEqual([
      { value: "1", label: "1 — Não" },
      { value: "2", label: "2 — Sim" },
    ]);
  });

  it("mantém o código quando não há rótulo cadastrado", () => {
    expect(enumOptions("unknownPath", ["X"])).toEqual([
      { value: "X", label: "X" },
    ]);
  });
});

describe("withSelectedOption", () => {
  it("injeta o valor selecionado ausente da lista", () => {
    const options = withSelectedOption(
      [{ value: "02", label: "02 — Fábrica" }],
      "01",
    );
    expect(options[0]).toEqual({
      value: "01",
      label: "01 — valor selecionado",
    });
    expect(options).toHaveLength(2);
  });

  it("não duplica quando o valor já está na lista", () => {
    const options = withSelectedOption(
      [{ value: "01", label: "01 — Almoxarifado" }],
      "01",
    );
    expect(options).toHaveLength(1);
  });

  it("sem seleção retorna a lista intacta", () => {
    const options = withSelectedOption([{ value: "A", label: "A" }], "");
    expect(options).toEqual([{ value: "A", label: "A" }]);
  });
});

describe("PrcCatalogStore", () => {
  it("idle → loading → success com itens reais", async () => {
    const d = deferred<Envelope<CatalogPayload>>();
    const fetchCatalog = vi.fn<FetchCatalog>(() => d.promise);
    const store = storeWith(fetchCatalog);

    expect(store.view("group").status).toBe("idle");
    store.load("group");
    expect(store.view("group").status).toBe("loading");

    d.resolve({
      success: true,
      message: "ok",
      data: { items: [item("1001", "Plásticos")], hasMore: false },
    });
    await vi.waitFor(() =>
      expect(store.view("group").status).toBe("success"),
    );
    expect(store.view("group").options).toEqual([
      { value: "1001", label: "1001 — Plásticos" },
    ]);
    expect(fetchCatalog).toHaveBeenCalledWith(
      "product-groups",
      undefined,
      expect.any(AbortSignal),
      PRC_CATALOG_PAGE_LIMIT,
    );
  });

  it("array vazio vira `empty`, nunca `error`", async () => {
    const fetchCatalog = vi.fn<FetchCatalog>(async () => ({
      success: true,
      message: "ok",
      data: { items: [], hasMore: false },
    }));
    const store = storeWith(fetchCatalog);
    store.load("unit");
    await vi.waitFor(() =>
      expect(store.view("unit").status).toBe("empty"),
    );
    expect(store.view("unit").options).toEqual([]);
  });

  it.each([
    ["unauthorized", "401"],
    ["forbidden", "403"],
    ["unavailable", "500/503"],
    ["timeout", "timeout"],
    ["contract_error", "resposta incompatível"],
    ["network_error", "falha de rede"],
  ])(
    "falha `%s` (%s) vira `error` com errorKind preservado",
    async (kind) => {
      const fetchCatalog = vi.fn<FetchCatalog>(async () => {
        throw { kind };
      });
      const store = storeWith(fetchCatalog);
      store.load("defaultWarehouse");
      await vi.waitFor(() =>
        expect(store.view("defaultWarehouse").status).toBe("error"),
      );
      expect(store.view("defaultWarehouse").errorKind).toBe(kind);
    },
  );

  it("retry após falha recarrega e conclui em success", async () => {
    let calls = 0;
    const fetchCatalog = vi.fn<FetchCatalog>(async () => {
      calls += 1;
      if (calls === 1) throw { kind: "unavailable" };
      return {
        success: true,
        message: "ok",
        data: { items: [item("UN", "Unidade")], hasMore: false },
      };
    });
    const store = storeWith(fetchCatalog);
    store.load("unit");
    await vi.waitFor(() =>
      expect(store.view("unit").status).toBe("error"),
    );

    store.retry("unit");
    expect(store.view("unit").status).toBe("loading");
    await vi.waitFor(() =>
      expect(store.view("unit").status).toBe("success"),
    );
    expect(fetchCatalog).toHaveBeenCalledTimes(2);
  });

  it("request obsoleta (retry) não sobrescreve a carga mais nova", async () => {
    const first = deferred<Envelope<CatalogPayload>>();
    const second = deferred<Envelope<CatalogPayload>>();
    const fetchCatalog = vi
      .fn<FetchCatalog>()
      .mockImplementationOnce(() => first.promise)
      .mockImplementationOnce(() => second.promise);
    const store = storeWith(fetchCatalog);

    store.load("group");
    store.retry("group");
    second.resolve({
      success: true,
      message: "ok",
      data: { items: [item("2000", "Novo")], hasMore: false },
    });
    await vi.waitFor(() =>
      expect(store.view("group").status).toBe("success"),
    );

    first.resolve({
      success: true,
      message: "ok",
      data: { items: [item("9999", "Velho")], hasMore: false },
    });
    await Promise.resolve();
    expect(store.view("group").options[0].value).toBe("2000");
  });

  it("abort do unmount impede escrita de estado", async () => {
    const d = deferred<Envelope<CatalogPayload>>();
    const fetchCatalog = vi.fn<FetchCatalog>((_c, _q, signal) => {
      signal?.addEventListener("abort", () => d.resolve({
        success: true,
        message: "ok",
        data: { items: [item("X")], hasMore: false },
      }));
      return d.promise;
    });
    const store = storeWith(fetchCatalog);
    const outer = new AbortController();
    store.load("group", outer.signal);
    outer.abort();
    await Promise.resolve();
    expect(store.view("group").status).toBe("loading");
  });

  it("mantém opções anteriores durante reload (valor preservado)", async () => {
    let calls = 0;
    const gates: Array<ReturnType<typeof deferred<Envelope<CatalogPayload>>>> = [
      deferred<Envelope<CatalogPayload>>(),
      deferred<Envelope<CatalogPayload>>(),
    ];
    const fetchCatalog = vi.fn<FetchCatalog>(() => {
      const gate = gates[calls++];
      return gate.promise;
    });
    const store = storeWith(fetchCatalog);
    store.load("group");
    gates[0].resolve({
      success: true,
      message: "ok",
      data: { items: [item("1001", "Plásticos")], hasMore: false },
    });
    await vi.waitFor(() =>
      expect(store.view("group").status).toBe("success"),
    );

    store.retry("group");
    const view = store.view("group");
    expect(view.status).toBe("loading");
    expect(view.options[0].value).toBe("1001");
  });

  it("erro após sucesso mantém opções e sinaliza errorKind", async () => {
    let calls = 0;
    const fetchCatalog = vi.fn<FetchCatalog>(async () => {
      calls += 1;
      if (calls === 2) throw { kind: "unavailable" };
      return {
        success: true,
        message: "ok",
        data: { items: [item("01", "Almoxarifado")], hasMore: false },
      };
    });
    const store = storeWith(fetchCatalog);
    store.load("defaultWarehouse");
    await vi.waitFor(() =>
      expect(store.view("defaultWarehouse").status).toBe("success"),
    );
    store.retry("defaultWarehouse");
    await vi.waitFor(() =>
      expect(store.view("defaultWarehouse").status).toBe("error"),
    );
    expect(store.view("defaultWarehouse").options[0].value).toBe("01");
  });

  it("hasMore verdadeiro é propagado para o hint de paginação", async () => {
    const fetchCatalog = vi.fn<FetchCatalog>(async () => ({
      success: true,
      message: "ok",
      data: { items: [item("1")], hasMore: true },
    }));
    const store = storeWith(fetchCatalog);
    store.load("accountingAccount");
    await vi.waitFor(() =>
      expect(store.view("accountingAccount").status).toBe("success"),
    );
    expect(store.view("accountingAccount").hasMore).toBe(true);
  });

  it("load em path sem catálogo é no-op seguro", () => {
    const fetchCatalog = vi.fn<FetchCatalog>();
    const store = storeWith(fetchCatalog);
    store.load("description");
    expect(store.view("description").status).toBe("idle");
    expect(fetchCatalog).not.toHaveBeenCalled();
  });
});
