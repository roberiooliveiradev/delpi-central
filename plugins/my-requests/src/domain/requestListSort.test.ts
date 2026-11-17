import { describe, expect, it } from "vitest";

import {
  MERGED_SORT_FIELDS,
  PRC_SORT_FIELDS,
  PRC_TYPE_CODE,
  REQUESTS_SORT_FIELDS,
  defaultSortLevels,
  headerSortDirection,
  parseListSortLevels,
  serializeListSortLevels,
  sortCatalogForSource,
  sourceForTypeCode,
} from "./requestListSort";

describe("requestListSort — fonte efetiva e catálogos", () => {
  it("sem tipo filtrado → conjunto mesclado (só Data, 1 nível)", () => {
    expect(sourceForTypeCode("")).toBe("merged");
    const catalog = sortCatalogForSource("merged");
    expect(catalog.fields).toEqual(MERGED_SORT_FIELDS);
    expect(catalog.maxLevels).toBe(1);
    expect(catalog.fields.map((f) => f.value)).toEqual(["created_at"]);
  });

  it("tipo requests-api comum → catálogo completo (3 níveis)", () => {
    expect(sourceForTypeCode("invoice-issuance")).toBe("requests");
    const catalog = sortCatalogForSource("requests");
    expect(catalog.maxLevels).toBe(3);
    expect(catalog.fields.map((f) => f.value)).toEqual([
      "created_at",
      "updated_at",
      "request_number",
      "status",
      "type_code",
      "branch",
      "requester",
      "completed_by",
    ]);
  });

  it("tipo PRC → mescla ainda é por Data (1 nível, campo comparável)", () => {
    expect(sourceForTypeCode(PRC_TYPE_CODE)).toBe("prc");
    const catalog = sortCatalogForSource("prc");
    expect(catalog.maxLevels).toBe(1);
    /* A fila PRC continua mesclada com requests-api — o merge só é
     * honesto pelo campo comparável (created_at), não pelos campos
     * exclusivos do contrato PRC. */
    expect(catalog.fields).toEqual(MERGED_SORT_FIELDS);
    /* O catálogo PRC completo fica exportado para uma futura lista
     * PRC isolada — não usado no merge unificado. */
    expect(PRC_SORT_FIELDS.length).toBeGreaterThan(1);
  });

  it("o catálogo requests-api cobre exatamente a whitelist do backend", () => {
    /* espelha LIST_SORT_FIELDS de requests-api/domain/request_list_sort */
    expect(REQUESTS_SORT_FIELDS.map((f) => f.value).sort()).toEqual(
      [
        "created_at",
        "updated_at",
        "request_number",
        "status",
        "type_code",
        "branch",
        "requester",
        "completed_by",
      ].sort(),
    );
  });
});

describe("requestListSort — parse/serialize", () => {
  it("serializa níveis no contrato field:dir", () => {
    expect(
      serializeListSortLevels([
        { field: "status", direction: "asc" },
        { field: "created_at", direction: "desc" },
      ]),
    ).toBe("status:asc,created_at:desc");
    expect(serializeListSortLevels([])).toBe("");
  });

  it("parse aceita só campos do catálogo e direções válidas", () => {
    expect(
      parseListSortLevels(
        "status:asc,created_at:desc",
        REQUESTS_SORT_FIELDS,
      ),
    ).toEqual([
      { field: "status", direction: "asc" },
      { field: "created_at", direction: "desc" },
    ]);
    /* campo fora do catálogo é ignorado (fonte trocou) */
    expect(
      parseListSortLevels("request_number:asc", MERGED_SORT_FIELDS),
    ).toEqual([]);
    /* direção inválida cai para desc */
    expect(
      parseListSortLevels("created_at:sideways", REQUESTS_SORT_FIELDS),
    ).toEqual([{ field: "created_at", direction: "desc" }]);
  });

  it("não duplica campo na mesma ordenação", () => {
    expect(
      parseListSortLevels(
        "status:asc,status:desc",
        REQUESTS_SORT_FIELDS,
      ),
    ).toEqual([{ field: "status", direction: "asc" }]);
  });

  it("defaults por fonte preservam Data desc", () => {
    expect(defaultSortLevels("merged")).toEqual([
      { field: "created_at", direction: "desc" },
    ]);
    /* fonte prc também usa created_at — campo aceito pelo requests-api
     * e equivalente ao createdAt da Engineering API no merge. */
    expect(defaultSortLevels("prc")).toEqual([
      { field: "created_at", direction: "desc" },
    ]);
  });
});

describe("headerSortDirection — convenção do primeiro clique", () => {
  it("campos de data (`*_at`) começam descendentes", () => {
    expect(headerSortDirection("created_at")).toBe("desc");
    expect(headerSortDirection("updated_at")).toBe("desc");
  });

  it("texto/códigos começam ascendentes", () => {
    expect(headerSortDirection("status")).toBe("asc");
    expect(headerSortDirection("type_code")).toBe("asc");
    expect(headerSortDirection("branch")).toBe("asc");
    expect(headerSortDirection("request_number")).toBe("asc");
  });
});
