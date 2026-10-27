/**
 * documentCatalog — derivação do catálogo por item_key a partir da
 * timeline de versões publicadas + delegação ao comando transacional
 * da BFF (GATE-015, DR-1/DR-2).
 */
import { afterEach, describe, expect, it, vi } from "vitest";

const saveRequirementMock = vi.fn();

vi.mock("../../api/adminApi", () => ({
  saveDocumentRequirement: (...args: unknown[]) =>
    saveRequirementMock(...args),
}));

import {
  catalogBaseVersion,
  deriveDocumentCatalog,
  endDocumentRequirement,
  formatPeriod,
  nextPeriod,
  previousPeriod,
  saveDocumentConfig,
  slugifyItemKey,
  sortPublished,
  toDraftItems,
  winnerAt,
  type DocumentFormPayload,
  type VersionWithItems,
} from "./documentCatalog";

const ITEM_A = {
  item_id: "i-a",
  item_key: "DOC-A",
  sort_order: 10,
  sheet: "ELETRONICO" as const,
  name: "Balancete",
  purpose: "Fechamento contábil",
  origin_kind: "TOTVS" as const,
  recipient_area: "CONTABIL" as const,
  applicability: "REQUIRED" as const,
  branch_scope: "BOTH" as const,
  totvs_report_ref: "MATR460",
  requirement_notes: null,
  validation_scope: "PER_ATTACHMENT" as const,
};

const ITEM_B = {
  ...ITEM_A,
  item_id: "i-b",
  item_key: "DOC-B",
  sort_order: 20,
  name: "Extrato bancário",
  purpose: null,
  recipient_area: null,
  applicability: "OPTIONAL" as const,
};

const ITEM_C = {
  ...ITEM_A,
  item_id: "i-c",
  item_key: "DOC-C",
  sort_order: 30,
  name: "Documento futuro",
};

function version(
  n: number,
  status: string,
  effective: string | null,
  items: (typeof ITEM_A)[],
): VersionWithItems {
  return {
    version_id: `v-${n}`,
    template_id: "t-1",
    version: n,
    status: status as VersionWithItems["status"],
    revision: 1,
    effective_from_period: effective,
    published_by: "user",
    published_at: "2026-01-01T00:00:00Z",
    inactivated_at: null,
    created_at: "2026-01-01T00:00:00Z",
    item_count: items.length,
    items,
  };
}

const DOC_C: DocumentFormPayload = {
  itemKey: "DOC-C",
  name: "Documento futuro",
  purpose: "Teste",
  originKind: "TOTVS",
  recipientArea: "CONTABIL",
  applicability: "REQUIRED",
  sheet: "ELETRONICO",
  branchScope: "BOTH",
  totvsReportRef: null,
  requirementNotes: null,
  validationScope: "PER_ATTACHMENT",
};

describe("documentCatalog — helpers", () => {
  it("nextPeriod/previousPeriod atravessam virada de ano", () => {
    expect(nextPeriod("2026-12")).toBe("2027-01");
    expect(nextPeriod("2026-05")).toBe("2026-06");
    expect(previousPeriod("2026-01")).toBe("2025-12");
    expect(previousPeriod("2026-10")).toBe("2026-09");
  });

  it("slugifyItemKey gera identificador estável e limitado", () => {
    expect(slugifyItemKey("Balanço Patrimonial")).toBe(
      "BALANCO-PATRIMONIAL",
    );
    expect(slugifyItemKey("NF-e saída 01/02")).toBe("NF-E-SAIDA-01-02");
    expect(slugifyItemKey("")).toBe("DOCUMENTO");
    expect(
      slugifyItemKey("a".repeat(60)).length,
    ).toBeLessThanOrEqual(32);
  });

  it("formatPeriod exibe MM/AAAA", () => {
    expect(formatPeriod("2026-10")).toBe("10/2026");
    expect(formatPeriod(null)).toBe("—");
  });

  it("toDraftItems preserva todos os campos do contrato", () => {
    const [draft] = toDraftItems([ITEM_A]);
    expect(draft).toMatchObject({
      item_key: "DOC-A",
      name: "Balancete",
      recipient_area: "CONTABIL",
      validation_scope: "PER_ATTACHMENT",
    });
    expect("item_id" in draft!).toBe(false);
  });
});

describe("timeline — winnerAt espelha resolve_published_version", () => {
  it("mesmo effective_from: a versão MAIOR vence (version DESC)", () => {
    const published = sortPublished([
      version(1, "PUBLISHED", "2026-01", [ITEM_A]),
      version(2, "PUBLISHED", "2026-01", [ITEM_A, ITEM_B]),
    ]);
    expect(winnerAt(published, "2026-03")?.version).toBe(2);
    expect(winnerAt(published, "2025-12")).toBeNull();
  });

  it("versão de maior NÚMERO com eff posterior não vence período anterior", () => {
    const published = sortPublished([
      version(1, "PUBLISHED", "2026-01", [ITEM_A]),
      version(5, "PUBLISHED", "2027-01", [ITEM_A, ITEM_B]),
    ]);
    expect(winnerAt(published, "2026-06")?.version).toBe(1);
    expect(winnerAt(published, "2027-02")?.version).toBe(5);
  });
});

describe("deriveDocumentCatalog", () => {
  it("deriva janelas de exigência da timeline publicada", () => {
    const rows = deriveDocumentCatalog(
      [
        version(1, "PUBLISHED", "2026-01", [ITEM_A, ITEM_B]),
        version(2, "PUBLISHED", "2026-04", [ITEM_A]),
      ],
      "2026-06",
    );
    const a = rows.find((r) => r.itemKey === "DOC-A")!;
    const b = rows.find((r) => r.itemKey === "DOC-B")!;
    expect(a.windows).toEqual([{ from: "2026-01", to: null }]);
    expect(a.situation).toBe("vigente");
    expect(b.windows).toEqual([{ from: "2026-01", to: "2026-03" }]);
    expect(b.situation).toBe("encerrado");
    expect(b.latestPublishedVersion).toBe(1);
  });

  it("marca documento somente futuro quando a vigência ainda não chegou", () => {
    const rows = deriveDocumentCatalog(
      [
        version(1, "PUBLISHED", "2026-01", [ITEM_A]),
        version(2, "PUBLISHED", "2026-09", [ITEM_A, ITEM_C]),
      ],
      "2026-06",
    );
    const c = rows.find((r) => r.itemKey === "DOC-C")!;
    expect(c.situation).toBe("futuro");
    expect(c.vigenciaInicial).toBe("2026-09");
  });

  it("item apenas em DRAFT aparece como futuro e pendente", () => {
    const rows = deriveDocumentCatalog(
      [
        version(1, "PUBLISHED", "2026-01", [ITEM_A]),
        version(2, "DRAFT", null, [ITEM_A, ITEM_C]),
      ],
      "2026-06",
    );
    const c = rows.find((r) => r.itemKey === "DOC-C")!;
    expect(c.situation).toBe("futuro");
    expect(c.pendingInDraft).toBe(true);
    const a = rows.find((r) => r.itemKey === "DOC-A")!;
    expect(a.situation).toBe("vigente");
  });

  it("janelas descontínuas (exigido → removido → reativado) são separadas", () => {
    const rows = deriveDocumentCatalog(
      [
        version(1, "PUBLISHED", "2026-01", [ITEM_A, ITEM_B]),
        version(2, "PUBLISHED", "2026-03", [ITEM_A]),
        version(3, "PUBLISHED", "2026-05", [ITEM_A, ITEM_B]),
      ],
      "2026-06",
    );
    const b = rows.find((r) => r.itemKey === "DOC-B")!;
    expect(b.windows).toEqual([
      { from: "2026-01", to: "2026-02" },
      { from: "2026-05", to: null },
    ]);
    expect(b.situation).toBe("vigente");
  });
});
describe("catalogBaseVersion — OCC do comando transacional", () => {
  it("retorna MAX(version) e 0 para timeline vazia", () => {
    expect(
      catalogBaseVersion([
        version(1, "PUBLISHED", "2026-01", [ITEM_A]),
        version(3, "DRAFT", null, [ITEM_A]),
        version(2, "PUBLISHED", "2026-04", [ITEM_A]),
      ]),
    ).toBe(3);
    expect(catalogBaseVersion([])).toBe(0);
  });
});

describe("saveDocumentConfig — comando único da BFF (DR-1)", () => {
  afterEach(() => vi.clearAllMocks());

  it("delega ao endpoint transacional com item, janela, base_version e key", async () => {
    saveRequirementMock.mockResolvedValue({ published_versions: [] });
    await saveDocumentConfig("t-1", DOC_C, "2026-08", "2026-10", {
      baseVersion: 7,
      idempotencyKey: "k-1",
    });
    expect(saveRequirementMock).toHaveBeenCalledWith(
      "t-1",
      "DOC-C",
      {
        item: expect.objectContaining({
          item_key: "DOC-C",
          name: "Documento futuro",
          recipient_area: "CONTABIL",
          validation_scope: "PER_ATTACHMENT",
        }),
        effective_from: "2026-08",
        effective_until: "2026-10",
        base_version: 7,
        allow_empty: false,
      },
      "k-1",
    );
    expect(saveRequirementMock).toHaveBeenCalledTimes(1);
  });

  it("vigência sem término envia effective_until null", async () => {
    saveRequirementMock.mockResolvedValue({ published_versions: [] });
    await saveDocumentConfig("t-1", DOC_C, "2026-08", null, {
      baseVersion: 3,
      idempotencyKey: "k-2",
    });
    expect(saveRequirementMock.mock.calls[0][2].effective_until).toBeNull();
  });

  it("propaga o resultado da BFF (published_versions/skipped/no_changes)", async () => {
    const result = { published_versions: [9], skipped: [], no_changes: false };
    saveRequirementMock.mockResolvedValue(result);
    await expect(
      saveDocumentConfig("t-1", DOC_C, "2026-08", null, {
        baseVersion: 3,
        idempotencyKey: "k-3",
      }),
    ).resolves.toBe(result);
  });
});

describe("endDocumentRequirement — encerramento pelo mesmo comando", () => {
  afterEach(() => vi.clearAllMocks());

  it("envia intenção de encerramento (item ausente) com allow_empty", async () => {
    saveRequirementMock.mockResolvedValue({ published_versions: [10] });
    await endDocumentRequirement("t-1", "DOC-A", "2026-07", {
      baseVersion: 5,
      idempotencyKey: "k-4",
      allowEmpty: true,
    });
    expect(saveRequirementMock).toHaveBeenCalledWith(
      "t-1",
      "DOC-A",
      {
        effective_from: "2026-07",
        base_version: 5,
        allow_empty: true,
      },
      "k-4",
    );
  });

  it("default allow_empty=false — esvaziamento acidental é barrado", async () => {
    saveRequirementMock.mockResolvedValue({ published_versions: [] });
    await endDocumentRequirement("t-1", "DOC-A", "2026-07", {
      baseVersion: 5,
      idempotencyKey: "k-5",
    });
    expect(saveRequirementMock.mock.calls[0][2].allow_empty).toBe(false);
  });
});
