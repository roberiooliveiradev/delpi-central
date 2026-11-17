/** MY-REQUESTS-JSON-PRESENTATION-CATALOG-TRANSITION-01 — catálogo JSON
 * de apresentação: validação, resolução por code, ordenação e fallback.
 * O JSON é copy visual — nunca autoridade operacional. */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  REQUEST_TYPE_CATALOG_VERSION,
  getRequestTypePresentation,
  parseRequestTypeCatalog,
  resolveRequestTypeCardCopy,
  sortRequestTypesByPresentation,
} from "./requestTypeCatalog";
import { requestTypeLabel } from "./presentationLabels";

const dir = dirname(fileURLToPath(import.meta.url));

const VALID = {
  version: 1,
  types: [
    { code: "a-type", title: "Tipo A", description: "Desc A", order: 10 },
    { code: "b-type", title: "Tipo B", description: "Desc B", order: 20 },
  ],
};

describe("requestTypeCatalog — carregamento e conteúdo", () => {
  it("JSON versionado carrega os dois tipos iniciais", () => {
    const raw = JSON.parse(
      readFileSync(resolve(dir, "requestTypeCatalog.json"), "utf-8"),
    );
    expect(raw.version).toBe(REQUEST_TYPE_CATALOG_VERSION);
    const entries = parseRequestTypeCatalog(raw);
    expect(entries.map((e) => e.code)).toEqual([
      "raw-material-creation",
      "invoice-issuance",
    ]);
    expect(entries[0].order).toBeLessThan(entries[1].order);
  });

  it("resolve apresentação por code; desconhecido retorna null", () => {
    const prc = getRequestTypePresentation("raw-material-creation");
    expect(prc?.title).toBe("Criação e alteração de matéria-prima");
    expect(prc?.description).toContain("matéria-prima");
    expect(getRequestTypePresentation("does-not-exist")).toBeNull();
    expect(getRequestTypePresentation(null)).toBeNull();
  });
});

describe("parseRequestTypeCatalog — validação", () => {
  it("aceita catálogo válido", () => {
    expect(parseRequestTypeCatalog(VALID)).toHaveLength(2);
  });

  it("rejeita versão incompatível", () => {
    expect(() =>
      parseRequestTypeCatalog({ ...VALID, version: 2 }),
    ).toThrow(/versão incompatível/);
  });

  it("rejeita código duplicado", () => {
    expect(() =>
      parseRequestTypeCatalog({
        version: 1,
        types: [VALID.types[0], { ...VALID.types[1], code: "a-type" }],
      }),
    ).toThrow(/duplicado/);
  });

  it("rejeita título vazio", () => {
    expect(() =>
      parseRequestTypeCatalog({
        version: 1,
        types: [{ code: "x", title: " ", description: "d", order: 1 }],
      }),
    ).toThrow(/title vazio/);
  });

  it("rejeita descrição vazia", () => {
    expect(() =>
      parseRequestTypeCatalog({
        version: 1,
        types: [{ code: "x", title: "t", description: "", order: 1 }],
      }),
    ).toThrow(/description vazio/);
  });

  it("rejeita ordenação ambígua (order repetida)", () => {
    expect(() =>
      parseRequestTypeCatalog({
        version: 1,
        types: [VALID.types[0], { ...VALID.types[1], order: 10 }],
      }),
    ).toThrow(/ordenação ambígua/);
  });
});

describe("apresentação — JSON vence texto técnico da API", () => {
  it("card usa título/descrição do JSON mesmo com name/description técnicos", () => {
    const copy = resolveRequestTypeCardCopy({
      code: "raw-material-creation",
      name: "RAW_MATERIAL_CREATE",
      description: "legacy technical desc",
    });
    expect(copy.title).toBe("Criação e alteração de matéria-prima");
    expect(copy.description).toContain("Solicite o cadastro");
    expect(copy.title).not.toBe("RAW_MATERIAL_CREATE");
  });

  it("fallback: tipo operacional sem entrada JSON usa textos da API", () => {
    const copy = resolveRequestTypeCardCopy({
      code: "other-type",
      name: "Outro tipo",
      description: "Desc da API",
    });
    expect(copy).toEqual({ title: "Outro tipo", description: "Desc da API" });
  });

  it("requestTypeLabel prefere JSON e segue coerente entre telas", () => {
    expect(requestTypeLabel("invoice-issuance", "INVOICE")).toBe(
      "Emissão de notas fiscais",
    );
    expect(requestTypeLabel("unknown-type", "Nome API")).toBe("Nome API");
    expect(requestTypeLabel("unknown-type")).toBe("Unknown type");
  });
});

describe("sortRequestTypesByPresentation", () => {
  it("ordena pela order do JSON e mantém API order nos não catalogados", () => {
    const sorted = sortRequestTypesByPresentation([
      { code: "z-uncatalogued" },
      { code: "invoice-issuance" },
      { code: "raw-material-creation" },
      { code: "a-uncatalogued" },
    ]);
    expect(sorted.map((t) => t.code)).toEqual([
      "raw-material-creation",
      "invoice-issuance",
      "z-uncatalogued",
      "a-uncatalogued",
    ]);
  });
});

describe("limites do catálogo", () => {
  it("entrada JSON sem tipo operacional não aparece na lista renderizada", () => {
    // O sort só reordena o que a API retornou: um code só-JSON nunca
    // vira card porque a fonte da lista é operacional (creatableTypes).
    const operational = [{ code: "raw-material-creation" }];
    expect(
      sortRequestTypesByPresentation(operational).map((t) => t.code),
    ).toEqual(["raw-material-creation"]);
    expect(getRequestTypePresentation("invoice-issuance")).not.toBeNull();
  });
});
