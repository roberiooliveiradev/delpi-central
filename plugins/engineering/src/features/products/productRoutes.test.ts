import { describe, expect, it } from "vitest";

import {
  PRODUCT_PATHS,
  resolveProductsPath,
} from "./productRoutes";
import {
  formatBytes,
  formatProductDate,
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
