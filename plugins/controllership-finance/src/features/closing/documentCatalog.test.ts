/**
 * documentCatalog — derivação do catálogo por item_key a partir da
 * timeline de versões publicadas + orquestração DRAFT→REVIEW→PUBLISHED.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

const createDraftMock = vi.fn();
const updateDraftMock = vi.fn();
const submitReviewMock = vi.fn();
const publishMock = vi.fn();

vi.mock("../../api/adminApi", () => ({
  createTemplateDraft: (...args: unknown[]) => createDraftMock(...args),
  updateTemplateDraft: (...args: unknown[]) => updateDraftMock(...args),
  submitVersionForReview: (...args: unknown[]) =>
    submitReviewMock(...args),
  publishTemplateVersion: (...args: unknown[]) => publishMock(...args),
}));

import {
  CatalogSaveError,
  deriveDocumentCatalog,
  formatPeriod,
  nextPeriod,
  previousPeriod,
  publishRemovalVersion,
  saveDocumentConfig,
  slugifyItemKey,
  toDraftItems,
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
  items: typeof ITEM_A[],
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

  it("janelas descontínuas (exigido → removido → exigido) são separadas", () => {
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

describe("saveDocumentConfig — orquestração", () => {
  afterEach(() => vi.clearAllMocks());

  function setupDraft(version = 5) {
    createDraftMock.mockResolvedValue({
      version_id: `v-${version}`,
      version,
      status: "DRAFT",
      revision: 1,
      effective_from_period: null,
    });
    updateDraftMock.mockResolvedValue({});
    submitReviewMock.mockResolvedValue({});
    publishMock.mockResolvedValue({});
  }

  it("cria documento: draft → update com base+delta → review → publish", async () => {
    setupDraft();
    await saveDocumentConfig(
      "t-1",
      [ITEM_A],
      {
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
      },
      "2026-08",
      null,
    );
    expect(createDraftMock).toHaveBeenCalledWith("t-1");
    const [, vNum, payload] = updateDraftMock.mock.calls[0];
    expect(vNum).toBe(5);
    expect(payload.revision).toBe(1);
    expect(payload.items.map((i: { item_key: string }) => i.item_key))
      .toEqual(["DOC-A", "DOC-C"]);
    expect(submitReviewMock).toHaveBeenCalledWith("t-1", 5);
    expect(publishMock).toHaveBeenCalledWith("t-1", 5, {
      effective_from_period: "2026-08",
    });
  });

  it("vigência final publica versão de remoção no período seguinte", async () => {
    setupDraft();
    await saveDocumentConfig(
      "t-1",
      [ITEM_A],
      {
        itemKey: "DOC-C",
        name: "Documento temporário",
        purpose: null,
        originKind: "EXTERNAL",
        recipientArea: null,
        applicability: "OPTIONAL",
        sheet: "FISICO",
        branchScope: "MATRIX",
        totvsReportRef: null,
        requirementNotes: null,
        validationScope: "WHOLE_SET",
      },
      "2026-08",
      "2026-10",
    );
    expect(createDraftMock).toHaveBeenCalledTimes(2);
    expect(publishMock).toHaveBeenNthCalledWith(1, "t-1", 5, {
      effective_from_period: "2026-08",
    });
    const removalPayload = updateDraftMock.mock.calls[1][2];
    expect(
      removalPayload.items.map(
        (i: { item_key: string }) => i.item_key,
      ),
    ).toEqual(["DOC-A"]);
    expect(publishMock).toHaveBeenNthCalledWith(2, "t-1", 5, {
      effective_from_period: "2026-11",
    });
  });

  it("edição substitui o item de mesma chave sem duplicar", async () => {
    setupDraft();
    await saveDocumentConfig(
      "t-1",
      [ITEM_A, ITEM_B],
      {
        itemKey: "DOC-A",
        name: "Balancete revisado",
        purpose: "Novo",
        originKind: "TOTVS",
        recipientArea: "FISCAL",
        applicability: "CONDITIONAL",
        sheet: "ELETRONICO",
        branchScope: "BOTH",
        totvsReportRef: "MATR460",
        requirementNotes: "Nota",
        validationScope: "PER_ATTACHMENT",
      },
      "2026-08",
      null,
    );
    const payload = updateDraftMock.mock.calls[0][2];
    expect(payload.items).toHaveLength(2);
    const edited = payload.items.find(
      (i: { item_key: string }) => i.item_key === "DOC-A",
    );
    expect(edited.name).toBe("Balancete revisado");
    expect(edited.recipient_area).toBe("FISCAL");
    expect(edited.sort_order).toBe(10);
  });
});

describe("publishRemovalVersion", () => {
  afterEach(() => vi.clearAllMocks());

  it("publica remoção no período seguinte ao término", async () => {
    createDraftMock.mockResolvedValue({
      version: 7,
      status: "DRAFT",
      revision: 2,
    });
    updateDraftMock.mockResolvedValue({});
    submitReviewMock.mockResolvedValue({});
    publishMock.mockResolvedValue({});
    await publishRemovalVersion("t-1", toDraftItems([ITEM_B]), "2026-06");
    const payload = updateDraftMock.mock.calls[0][2];
    expect(
      payload.items.map((i: { item_key: string }) => i.item_key),
    ).toEqual(["DOC-B"]);
    expect(publishMock).toHaveBeenCalledWith("t-1", 7, {
      effective_from_period: "2026-07",
    });
  });

  it("recusa encerrar o único documento do checklist", async () => {
    await expect(
      publishRemovalVersion("t-1", [], "2026-06"),
    ).rejects.toBeInstanceOf(CatalogSaveError);
    expect(createDraftMock).not.toHaveBeenCalled();
  });
});
