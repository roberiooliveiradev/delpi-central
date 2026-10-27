/**
 * documentCatalog — derivação do catálogo por item_key a partir da
 * timeline de versões publicadas + plano de publicação idempotente e
 * orquestração DRAFT→REVIEW→PUBLISHED (RW01).
 */
import { afterEach, describe, expect, it, vi } from "vitest";

const createDraftMock = vi.fn();
const updateDraftMock = vi.fn();
const submitReviewMock = vi.fn();
const publishMock = vi.fn();
const listVersionsMock = vi.fn();
const getVersionMock = vi.fn();

vi.mock("../../api/adminApi", () => ({
  createTemplateDraft: (...args: unknown[]) => createDraftMock(...args),
  updateTemplateDraft: (...args: unknown[]) => updateDraftMock(...args),
  submitVersionForReview: (...args: unknown[]) =>
    submitReviewMock(...args),
  publishTemplateVersion: (...args: unknown[]) => publishMock(...args),
  listTemplateVersions: (...args: unknown[]) => listVersionsMock(...args),
  getTemplateVersion: (...args: unknown[]) => getVersionMock(...args),
}));

import {
  CatalogSaveError,
  deriveDocumentCatalog,
  formatPeriod,
  nextPeriod,
  planDocumentSave,
  previousPeriod,
  publishRemovalVersion,
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

/** Payload com configuração idêntica a ITEM_C (igualdade de conteúdo). */
const DOC_C_MATCH: DocumentFormPayload = {
  itemKey: "DOC-C",
  name: "Documento futuro",
  purpose: "Fechamento contábil",
  originKind: "TOTVS",
  recipientArea: "CONTABIL",
  applicability: "REQUIRED",
  sheet: "ELETRONICO",
  branchScope: "BOTH",
  totvsReportRef: "MATR460",
  requirementNotes: null,
  validationScope: "PER_ATTACHMENT",
};

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

/** Stub de listTemplateVersions+getTemplateVersion para a orquestração. */
function stubVersionFetch(versions: VersionWithItems[]) {
  listVersionsMock.mockResolvedValue(
    versions.map((v) => ({ ...v, items: undefined })),
  );
  getVersionMock.mockImplementation((_t: string, n: number) =>
    Promise.resolve(versions.find((v) => v.version === n)),
  );
}

function setupDraft() {
  let next = 90;
  createDraftMock.mockImplementation(() =>
    Promise.resolve({
      version_id: `v-${next}`,
      version: next++,
      status: "DRAFT",
      revision: 1,
      effective_from_period: null,
    }),
  );
  updateDraftMock.mockResolvedValue({});
  submitReviewMock.mockResolvedValue({});
  publishMock.mockResolvedValue({});
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

describe("planDocumentSave — propagação por boundary (RW01-B)", () => {
  it("inclui o item em TODOS os boundaries futuros cobertos", () => {
    // v1: A desde 2026-11; v2: A+C desde 2027-01 — salvar B em 2026-12
    // precisa propagar B para o boundary 2027-01 também.
    const steps = planDocumentSave(
      [
        version(1, "PUBLISHED", "2026-11", [ITEM_A]),
        version(2, "PUBLISHED", "2027-01", [ITEM_A, ITEM_C]),
      ],
      { ...DOC_C, itemKey: "DOC-B", name: "Extrato" },
      "2026-12",
      null,
    );
    expect(steps.map((s) => s.effectiveFrom)).toEqual([
      "2026-12",
      "2027-01",
    ]);
    expect(
      steps[0].items.map((i) => i.item_key).sort(),
    ).toEqual(["DOC-A", "DOC-B"]);
    expect(
      steps[1].items.map((i) => i.item_key).sort(),
    ).toEqual(["DOC-A", "DOC-B", "DOC-C"]);
  });

  it("com término, não propaga além do until e publica remoção em until+1", () => {
    const steps = planDocumentSave(
      [
        version(1, "PUBLISHED", "2026-11", [ITEM_A]),
        version(2, "PUBLISHED", "2027-01", [ITEM_A, ITEM_C]),
      ],
      { ...DOC_C, itemKey: "DOC-B", name: "Temporário" },
      "2026-12",
      "2027-02",
    );
    const effs = steps.map((s) => s.effectiveFrom);
    // 2026-12 (inclusão), 2027-01 (propagação), 2027-03 (remoção).
    expect(effs).toEqual(["2026-12", "2027-01", "2027-03"]);
    const removal = steps[2];
    expect(removal.items.map((i) => i.item_key).sort()).toEqual([
      "DOC-A",
      "DOC-C",
    ]);
  });

  it("omite passos cuja configuração já é a vigente (idempotência)", () => {
    // B já exigido nos dois boundaries → nada a publicar.
    const steps = planDocumentSave(
      [
        version(1, "PUBLISHED", "2026-11", [ITEM_A, ITEM_B]),
        version(2, "PUBLISHED", "2027-01", [ITEM_A, ITEM_B, ITEM_C]),
      ],
      {
        itemKey: "DOC-B",
        name: "Extrato bancário",
        purpose: null,
        originKind: "TOTVS",
        recipientArea: null,
        applicability: "OPTIONAL",
        sheet: "ELETRONICO",
        branchScope: "BOTH",
        totvsReportRef: "MATR460",
        requirementNotes: null,
        validationScope: "PER_ATTACHMENT",
      },
      "2026-11",
      null,
    );
    expect(steps).toEqual([]);
  });

  it("edição substitui a configuração futura do item nos boundaries", () => {
    const edited: DocumentFormPayload = {
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
    };
    const steps = planDocumentSave(
      [
        version(1, "PUBLISHED", "2026-01", [ITEM_A, ITEM_B]),
        version(2, "PUBLISHED", "2026-05", [ITEM_A, ITEM_B, ITEM_C]),
      ],
      edited,
      "2026-03",
      null,
    );
    expect(steps.map((s) => s.effectiveFrom)).toEqual([
      "2026-03",
      "2026-05",
    ]);
    for (const step of steps) {
      const a = step.items.find((i) => i.item_key === "DOC-A")!;
      expect(a.name).toBe("Balancete revisado");
      expect(a.recipient_area).toBe("FISCAL");
      expect(a.sort_order).toBe(10);
    }
    expect(steps[1].items.map((i) => i.item_key)).toContain("DOC-C");
  });
});

describe("saveDocumentConfig — orquestração", () => {
  afterEach(() => vi.clearAllMocks());

  it("cria documento: draft → update com base do vencedor → review → publish", async () => {
    stubVersionFetch([version(1, "PUBLISHED", "2026-01", [ITEM_A])]);
    setupDraft();
    await saveDocumentConfig("t-1", DOC_C, "2026-08", null);
    expect(createDraftMock).toHaveBeenCalledWith("t-1");
    const [, vNum, payload] = updateDraftMock.mock.calls[0];
    expect(vNum).toBe(90);
    expect(payload.revision).toBe(1);
    expect(payload.items.map((i: { item_key: string }) => i.item_key))
      .toEqual(["DOC-A", "DOC-C"]);
    expect(submitReviewMock).toHaveBeenCalledWith("t-1", 90);
    expect(publishMock).toHaveBeenCalledWith("t-1", 90, {
      effective_from_period: "2026-08",
    });
  });

  it("vigência final publica remoção em until+1 com base do vencedor", async () => {
    stubVersionFetch([version(1, "PUBLISHED", "2026-01", [ITEM_A])]);
    setupDraft();
    await saveDocumentConfig(
      "t-1",
      { ...DOC_C, name: "Temporário" },
      "2026-08",
      "2026-10",
    );
    expect(createDraftMock).toHaveBeenCalledTimes(2);
    expect(publishMock).toHaveBeenNthCalledWith(1, "t-1", 90, {
      effective_from_period: "2026-08",
    });
    const removalPayload = updateDraftMock.mock.calls[1][2];
    expect(
      removalPayload.items.map(
        (i: { item_key: string }) => i.item_key,
      ),
    ).toEqual(["DOC-A"]);
    expect(publishMock).toHaveBeenNthCalledWith(2, "t-1", 91, {
      effective_from_period: "2026-11",
    });
  });

  it("base é o vencedor do boundary — não a versão de maior número", async () => {
    // v2 é de REMOÇÃO futura (sem A): salvar doc em 2026-06 não pode
    // encurtar a exigência de A que vale até 2026-11.
    stubVersionFetch([
      version(1, "PUBLISHED", "2026-01", [ITEM_A]),
      version(2, "PUBLISHED", "2026-12", []),
    ]);
    setupDraft();
    await saveDocumentConfig("t-1", DOC_C, "2026-06", "2026-08");
    const firstPayload = updateDraftMock.mock.calls[0][2];
    expect(
      firstPayload.items.map((i: { item_key: string }) => i.item_key),
    ).toEqual(["DOC-A", "DOC-C"]);
    // Remoção em 2026-09: vencedor é v1 (A) → alvo A sem C.
    const removalPayload = updateDraftMock.mock.calls[1][2];
    expect(
      removalPayload.items.map((i: { item_key: string }) => i.item_key),
    ).toEqual(["DOC-A"]);
  });

  it("retry após falha: passo já publicado é pulado (sem duplicar)", async () => {
    // Simula estado pós-falha: versão de inclusão já publicada.
    stubVersionFetch([
      version(1, "PUBLISHED", "2026-01", [ITEM_A]),
      version(2, "PUBLISHED", "2026-08", [ITEM_A, ITEM_C]),
    ]);
    setupDraft();
    await saveDocumentConfig("t-1", DOC_C_MATCH, "2026-08", "2026-10");
    // Só o passo de remoção é necessário.
    expect(createDraftMock).toHaveBeenCalledTimes(1);
    expect(publishMock).toHaveBeenCalledTimes(1);
    expect(publishMock).toHaveBeenCalledWith("t-1", 90, {
      effective_from_period: "2026-11",
    });
  });

  it("retoma versão REVIEW com itens iguais ao alvo (resume)", async () => {
    stubVersionFetch([
      version(1, "PUBLISHED", "2026-01", [ITEM_A]),
      version(2, "REVIEW", null, [ITEM_A, ITEM_C]),
    ]);
    await saveDocumentConfig("t-1", DOC_C_MATCH, "2026-08", null);
    // Sem draft novo: a versão REVIEW 2 é publicada diretamente.
    expect(createDraftMock).not.toHaveBeenCalled();
    expect(publishMock).toHaveBeenCalledWith("t-1", 2, {
      effective_from_period: "2026-08",
    });
  });

  it("rascunho aberto com conteúdo divergente vira conflito honesto", async () => {
    stubVersionFetch([
      version(1, "PUBLISHED", "2026-01", [ITEM_A]),
      version(2, "DRAFT", null, [ITEM_A, ITEM_B]),
    ]);
    await expect(
      saveDocumentConfig("t-1", DOC_C, "2026-08", null),
    ).rejects.toMatchObject({ code: "catalog_draft_conflict" });
    expect(publishMock).not.toHaveBeenCalled();
  });

  it("falha intermediária propaga o erro — nunca sucesso parcial", async () => {
    stubVersionFetch([version(1, "PUBLISHED", "2026-01", [ITEM_A])]);
    setupDraft();
    publishMock
      .mockResolvedValueOnce({})
      .mockRejectedValueOnce(new Error("publish failed"));
    await expect(
      saveDocumentConfig("t-1", DOC_C, "2026-08", "2026-10"),
    ).rejects.toThrow("publish failed");
  });
});

describe("publishRemovalVersion", () => {
  afterEach(() => vi.clearAllMocks());

  it("publica remoção no período seguinte ao término", async () => {
    stubVersionFetch([
      version(1, "PUBLISHED", "2026-01", [ITEM_A, ITEM_B]),
    ]);
    setupDraft();
    await publishRemovalVersion("t-1", "DOC-A", "2026-06");
    const payload = updateDraftMock.mock.calls[0][2];
    expect(
      payload.items.map((i: { item_key: string }) => i.item_key),
    ).toEqual(["DOC-B"]);
    expect(publishMock).toHaveBeenCalledWith("t-1", 90, {
      effective_from_period: "2026-07",
    });
  });

  it("remoção já vigente é no-op", async () => {
    stubVersionFetch([version(1, "PUBLISHED", "2026-01", [ITEM_A])]);
    await publishRemovalVersion("t-1", "DOC-B", "2026-06");
    expect(createDraftMock).not.toHaveBeenCalled();
    expect(publishMock).not.toHaveBeenCalled();
  });

  it("recusa encerrar o único documento do checklist", async () => {
    stubVersionFetch([version(1, "PUBLISHED", "2026-01", [ITEM_A])]);
    await expect(
      publishRemovalVersion("t-1", "DOC-A", "2026-06"),
    ).rejects.toBeInstanceOf(CatalogSaveError);
    expect(createDraftMock).not.toHaveBeenCalled();
  });
});
