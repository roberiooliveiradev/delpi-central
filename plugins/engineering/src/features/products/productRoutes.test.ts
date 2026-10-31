import { describe, expect, it } from "vitest";

import {
  PRODUCT_PATHS,
  buildProductsListUrl,
  parseProductTab,
  parseProductsListUrl,
  productDetailTabPath,
  resolveProductsPath,
} from "./productRoutes";
import {
  formatBytes,
  formatProductDate,
  productDescriptionDisplay,
  productStatusLabel,
  productTypeLabel,
} from "./productCopy";

describe("resolveProductsPath", () => {
  it("resolve a listagem", () => {
    expect(resolveProductsPath("products")).toEqual({ kind: "list" });
    expect(resolveProductsPath("")).toEqual({ kind: "list" });
    expect(resolveProductsPath("products/")).toEqual({ kind: "list" });
  });

  it("resolve o detalhe por código", () => {
    expect(resolveProductsPath("products/90269001")).toEqual({
      kind: "detail",
      code: "90269001",
    });
    expect(resolveProductsPath("products/PA-1234")).toEqual({
      kind: "detail",
      code: "PA-1234",
    });
  });

  it("decodifica código url-encoded", () => {
    expect(resolveProductsPath("products/A%20B")).toEqual({
      kind: "detail",
      code: "A B",
    });
  });

  it("marca caminhos desconhecidos como not_found", () => {
    expect(resolveProductsPath("products/a/b")).toEqual({
      kind: "not_found",
    });
  });

  it("monta paths de destino", () => {
    expect(PRODUCT_PATHS.detail("90269001")).toBe(
      "/apps/engineering/products/90269001",
    );
    expect(PRODUCT_PATHS.detail("A B")).toBe(
      "/apps/engineering/products/A%20B",
    );
  });
});

describe("productCopy helpers", () => {
  it("formata data ISO para pt-BR", () => {
    expect(formatProductDate("2026-01-15")).toBe("15/01/2026");
    expect(formatProductDate(null)).toBe("—");
    expect(formatProductDate("15/01/2026")).toBe("15/01/2026");
  });

  it("formata bytes", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
    expect(formatBytes(3 * 1024 * 1024)).toBe("3.0 MB");
    expect(formatBytes(null)).toBe("—");
  });

  it("rotula situação sem inventar estado", () => {
    expect(productStatusLabel({ blocked: "1", active: "1" })).toBe(
      "Bloqueado",
    );
    expect(productStatusLabel({ blocked: "0", active: "0" })).toBe(
      "Inativo",
    );
    expect(productStatusLabel({ blocked: "0", active: "1" })).toBe("Ativo");
  });

  it("rotula tipo com fallback honesto", () => {
    expect(productTypeLabel("MP")).toBe("Matéria-prima");
    expect(productTypeLabel("XX")).toBe("XX");
    expect(productTypeLabel(null)).toBe("—");
  });
});

describe("abas da ficha orientadas por URL (?tab=)", () => {
  it("aba ausente resolve overview", () => {
    expect(parseProductTab("")).toBe("overview");
    expect(parseProductTab("?x=1")).toBe("overview");
  });

  it("resolve todas as abas oficiais", () => {
    for (const key of [
      "overview",
      "structure",
      "where-used",
      "suppliers",
      "drawings",
      "history",
    ]) {
      expect(parseProductTab(`?tab=${key}`)).toBe(key);
    }
  });

  it("normaliza legado camelCase e valores inválidos para overview", () => {
    expect(parseProductTab("?tab=whereUsed")).toBe("where-used");
    expect(parseProductTab("?tab=invented")).toBe("overview");
    expect(parseProductTab("?tab=")).toBe("overview");
  });

  it("monta URL de aba — overview limpa o parâmetro", () => {
    expect(productDetailTabPath("30190123", "overview")).toBe(
      "/apps/engineering/products/30190123",
    );
    expect(productDetailTabPath("30190123", "structure")).toBe(
      "/apps/engineering/products/30190123?tab=structure",
    );
  });
});

describe("estado da listagem orientado por URL", () => {
  it("URL vazia produz estado inicial", () => {
    expect(parseProductsListUrl("")).toEqual({
      code: "",
      description: "",
      customer_reference: "",
      subgroup: "",
      groups: [],
      types: [],
      sort: null,
      direction: "asc",
      page: 1,
    });
  });

  it("parseia filtros, CSV multivalor, sort e página", () => {
    const state = parseProductsListUrl(
      "?code=30&description=ANEL&groups=3019,3020&types=MP,PA&ref=R1&sub=02&sort=code&dir=desc&page=3",
    );
    expect(state).toEqual({
      code: "30",
      description: "ANEL",
      customer_reference: "R1",
      subgroup: "02",
      groups: ["3019", "3020"],
      types: ["MP", "PA"],
      sort: "code",
      direction: "desc",
      page: 3,
    });
  });

  it("normaliza página inválida e direção desconhecida", () => {
    const state = parseProductsListUrl("?page=abc&dir=sideways");
    expect(state.page).toBe(1);
    expect(state.direction).toBe("asc");
  });

  it("roundtrip build↔parse preserva o estado", () => {
    const url = buildProductsListUrl({
      code: "90",
      description: "",
      customer_reference: "",
      subgroup: "02",
      groups: ["3019"],
      types: ["MP", "PI"],
      sort: "description",
      direction: "desc",
      page: 2,
    });
    expect(url).toContain("?");
    expect(url).toContain("sub=02");
    expect(parseProductsListUrl(url.split("?")[1])).toEqual({
      code: "90",
      description: "",
      customer_reference: "",
      subgroup: "02",
      groups: ["3019"],
      types: ["MP", "PI"],
      sort: "description",
      direction: "desc",
      page: 2,
    });
  });

  it("estado limpo gera URL sem query (botão Limpar)", () => {
    expect(
      buildProductsListUrl({
        code: "",
        description: "",
        customer_reference: "",
        subgroup: "",
        groups: [],
        types: [],
        sort: null,
        direction: "asc",
        page: 1,
      }),
    ).toBe("/apps/engineering/products");
  });
});

describe("descrições placeholder honestas (GATE E)", () => {
  it("sinaliza '#' e '###' como não informativos sem inventar texto", () => {
    expect(productDescriptionDisplay("#")).toEqual({
      text: "#",
      informative: false,
    });
    expect(productDescriptionDisplay("###")).toEqual({
      text: "###",
      informative: false,
    });
  });

  it("preserva descrições reais", () => {
    expect(productDescriptionDisplay("ANEL ORING 25X2")).toEqual({
      text: "ANEL ORING 25X2",
      informative: true,
    });
  });

  it("vazio/null vira traço neutro", () => {
    expect(productDescriptionDisplay(null)).toEqual({
      text: "—",
      informative: false,
    });
    expect(productDescriptionDisplay("  ")).toEqual({
      text: "—",
      informative: false,
    });
  });
});
