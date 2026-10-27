/**
 * Catálogo mestre de documentos do fechamento — UX-012 / RW01.
 *
 * O contrato da BFF é versionado e atômico (`/admin/checklist-templates*`):
 * cada versão publicada define o conjunto COMPLETO de exigências a partir
 * de `effective_from_period`, e a versão vencedora de uma competência é
 * `PUBLISHED` com `effective_from <= competência`, desempatando por
 * `version DESC` (resolve_published_version).
 *
 * RW01 — invariantes corrigidos:
 * - A base de cada publicação é a versão VENCEDORA no boundary, nunca a
 *   versão de maior número (que pode ser futura, de remoção ou INACTIVE).
 * - Inserir/editar exigência no meio da timeline PROPAGA o item aos
 *   boundaries futuros (até `until`), porque versões são conjuntos
 *   absolutos — sem propagação a exigência morreria no boundary seguinte.
 * - Cada passo de publicação é idempotente: se a configuração vigente no
 *   boundary já é o alvo, o passo é pulado — retry nunca duplica versão.
 * - Resume sem identidade: versão DRAFT/REVIEW com itens IGUAIS ao alvo é
 *   reutilizada (igualdade de conteúdo ⇒ publicar é equivalente); versão
 *   aberta com conteúdo diferente vira conflito honesto — nunca pisamos
 *   trabalho de outro administrador.
 * - Falha intermediária nunca informa sucesso: o erro sobe e o retry
 *   converge pelo plano idempotente. Atomicidade multi-versão verdadeira
 *   não existe no contrato — registrado em DECISION_REQUIRED.
 *
 * Snapshots de competências abertas/encerradas são cópia congelada —
 * nada aqui os reescreve.
 */
import {
  createTemplateDraft,
  getTemplateVersion,
  listTemplateVersions,
  publishTemplateVersion,
  submitVersionForReview,
  updateTemplateDraft,
  type ChecklistTemplateItem,
  type ChecklistTemplateVersion,
  type ChecklistTemplateVersionDetail,
  type DraftItemInput,
} from "../../api/adminApi";

export const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

export class CatalogSaveError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "CatalogSaveError";
    this.code = code;
  }
}

export type DocumentSituation = "vigente" | "futuro" | "encerrado";

export type RequirementWindow = { from: string; to: string | null };

export type DocumentCatalogRow = {
  itemKey: string;
  name: string;
  purpose: string | null;
  applicability: ChecklistTemplateItem["applicability"];
  recipientArea: ChecklistTemplateItem["recipient_area"];
  originKind: ChecklistTemplateItem["origin_kind"];
  sheet: ChecklistTemplateItem["sheet"];
  branchScope: ChecklistTemplateItem["branch_scope"];
  totvsReportRef: string | null;
  requirementNotes: string | null;
  validationScope: ChecklistTemplateItem["validation_scope"];
  /** Janelas de exigência derivadas da timeline de versões publicadas. */
  windows: RequirementWindow[];
  vigenciaInicial: string | null;
  vigenciaFinal: string | null;
  situation: DocumentSituation;
  /** Versão publicada mais recente que contém o item (proveniência). */
  latestPublishedVersion: number | null;
  /** Item existe em versão DRAFT/REVIEW ainda não publicada. */
  pendingInDraft: boolean;
};

export type VersionWithItems = ChecklistTemplateVersion & {
  items: ChecklistTemplateItem[];
};

export const APPLICABILITY_LABELS: Record<string, string> = {
  REQUIRED: "Obrigatório",
  CONDITIONAL: "Condicional",
  OPTIONAL: "Opcional",
};

export const RECIPIENT_LABELS: Record<string, string> = {
  CONTABIL: "Contabilidade",
  FISCAL: "Fiscal",
};

export const SITUATION_LABELS: Record<DocumentSituation, string> = {
  vigente: "Vigente",
  futuro: "Futuro",
  encerrado: "Encerrado",
};

export function currentPeriod(now = new Date()): string {
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}

export function nextPeriod(period: string): string {
  const [year, month] = period.split("-").map(Number);
  return month === 12
    ? `${year + 1}-01`
    : `${year}-${String(month + 1).padStart(2, "0")}`;
}

export function previousPeriod(period: string): string {
  const [year, month] = period.split("-").map(Number);
  return month === 1
    ? `${year - 1}-12`
    : `${year}-${String(month - 1).padStart(2, "0")}`;
}

/** Competência «AAAA-MM» → «MM/AAAA» para exibição. */
export function formatPeriod(period: string | null): string {
  if (!period) return "—";
  const [year, month] = period.split("-");
  return `${month}/${year}`;
}

/** Identificador técnico estável a partir do nome (identidade, ≤32). */
export function slugifyItemKey(name: string): string {
  const slug = name
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^\x20-\x7E]/g, "")
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 32);
  return slug || "DOCUMENTO";
}

export function toDraftItems(
  items: ChecklistTemplateItem[],
): DraftItemInput[] {
  return items.map((item) => ({
    item_key: item.item_key,
    sort_order: item.sort_order,
    sheet: item.sheet,
    name: item.name,
    purpose: item.purpose,
    origin_kind: item.origin_kind,
    recipient_area: item.recipient_area,
    applicability: item.applicability,
    branch_scope: item.branch_scope,
    totvs_report_ref: item.totvs_report_ref,
    requirement_notes: item.requirement_notes,
    validation_scope: item.validation_scope,
  }));
}

/* ------------------------------------------------------------------ */
/* Timeline canônica — mesma regra de `resolve_published_version`.       */
/* ------------------------------------------------------------------ */

/** Versões PUBLISHED ordenadas como o backend resolve (eff, version). */
export function sortPublished(
  versions: VersionWithItems[],
): VersionWithItems[] {
  return versions
    .filter(
      (v) => v.status === "PUBLISHED" && v.effective_from_period !== null,
    )
    .sort(
      (a, b) =>
        (a.effective_from_period ?? "").localeCompare(
          b.effective_from_period ?? "",
        ) || a.version - b.version,
    );
}

/** Versão vencedora de `period`: PUBLISHED, eff ≤ period, (eff, version) máx. */
export function winnerAt(
  published: VersionWithItems[],
  period: string,
): VersionWithItems | null {
  let winner: VersionWithItems | null = null;
  for (const version of published) {
    if ((version.effective_from_period ?? "") <= period) {
      winner = version;
    }
  }
  return winner;
}

/** Boundaries distintos da timeline publicada, em ordem crescente. */
export function timelineBoundaries(
  published: VersionWithItems[],
): string[] {
  return [
    ...new Set(
      published
        .map((v) => v.effective_from_period)
        .filter((p): p is string => p !== null),
    ),
  ].sort();
}

/* ------------------------------------------------------------------ */
/* Comparação de conteúdo — skip idempotente e resume por igualdade.     */
/* ------------------------------------------------------------------ */

type ItemFingerprint = string;

function itemFingerprint(item: DraftItemInput): ItemFingerprint {
  return JSON.stringify([
    item.item_key,
    item.name,
    item.purpose ?? null,
    item.origin_kind,
    item.recipient_area ?? null,
    item.applicability ?? "REQUIRED",
    item.branch_scope ?? "BOTH",
    item.sheet,
    item.totvs_report_ref ?? null,
    item.requirement_notes ?? null,
    item.validation_scope ?? "PER_ATTACHMENT",
  ]);
}

/** Conjunto de itens normalizado (ordem/sort_order não são semântica). */
function itemsFingerprintSet(
  items: readonly (DraftItemInput | ChecklistTemplateItem)[],
): Set<ItemFingerprint> {
  return new Set(items.map(itemFingerprint));
}

/** Igualdade estrutural de dois conjuntos de itens. */
export function itemsEqual(
  a: readonly (DraftItemInput | ChecklistTemplateItem)[],
  b: readonly (DraftItemInput | ChecklistTemplateItem)[],
): boolean {
  const fa = itemsFingerprintSet(a);
  if (fa.size !== b.length) return false;
  return b.every((item) => fa.has(itemFingerprint(item)));
}

/* ------------------------------------------------------------------ */
/* Derivação do catálogo — janelas de exigência por item_key.            */
/* ------------------------------------------------------------------ */

/**
 * Janelas de exigência de um item: a versão vencedora em cada fronteira
 * da timeline decide se o item é exigido naquele intervalo.
 */
function requirementWindows(
  published: VersionWithItems[],
  itemKey: string,
): RequirementWindow[] {
  const boundaries = timelineBoundaries(published);
  if (boundaries.length === 0) return [];
  const windows: RequirementWindow[] = [];
  let openFrom: string | null = null;
  boundaries.forEach((boundary, index) => {
    const winner = winnerAt(published, boundary);
    const required = Boolean(
      winner?.items.some((item) => item.item_key === itemKey),
    );
    const isLast = index === boundaries.length - 1;
    if (required) {
      if (openFrom === null) openFrom = boundary;
      if (isLast) {
        windows.push({ from: openFrom, to: null });
        openFrom = null;
      }
    } else if (openFrom !== null) {
      // A exigência terminou neste boundary: vigente até o período
      // imediatamente anterior.
      windows.push({ from: openFrom, to: previousPeriod(boundary) });
      openFrom = null;
    }
  });
  return windows;
}

/**
 * Agrega itens por `item_key` a partir das versões do template —
 * configuração mais recente publicada (ou de rascunho se nunca publicada)
 * e janelas de vigência derivadas.
 */
export function deriveDocumentCatalog(
  versions: VersionWithItems[],
  referencePeriod = currentPeriod(),
): DocumentCatalogRow[] {
  const published = sortPublished(versions);
  const pending = versions.filter(
    (v) => v.status === "DRAFT" || v.status === "REVIEW",
  );
  const rows = new Map<string, DocumentCatalogRow>();
  const source = [...versions].sort((a, b) => a.version - b.version);
  for (const version of source) {
    for (const item of version.items) {
      const existing = rows.get(item.item_key);
      const isPublished = version.status === "PUBLISHED";
      const row: DocumentCatalogRow = {
        itemKey: item.item_key,
        name: item.name,
        purpose: item.purpose,
        applicability: item.applicability,
        recipientArea: item.recipient_area,
        originKind: item.origin_kind,
        sheet: item.sheet,
        branchScope: item.branch_scope,
        totvsReportRef: item.totvs_report_ref,
        requirementNotes: item.requirement_notes,
        validationScope: item.validation_scope,
        windows: [],
        vigenciaInicial: null,
        vigenciaFinal: null,
        situation: "futuro",
        latestPublishedVersion:
          isPublished
            ? version.version
            : (existing?.latestPublishedVersion ?? null),
        pendingInDraft:
          existing?.pendingInDraft || !isPublished,
      };
      // A configuração exibida vem da versão mais recente que contém a
      // chave — rascunho só assume se o item nunca foi publicado.
      if (isPublished || existing?.latestPublishedVersion == null) {
        rows.set(item.item_key, row);
      } else {
        rows.set(item.item_key, {
          ...row,
          name: existing.name,
          purpose: existing.purpose,
          applicability: existing.applicability,
          recipientArea: existing.recipientArea,
          originKind: existing.originKind,
          sheet: existing.sheet,
          branchScope: existing.branchScope,
          totvsReportRef: existing.totvsReportRef,
          requirementNotes: existing.requirementNotes,
          validationScope: existing.validationScope,
        });
      }
    }
  }
  for (const row of rows.values()) {
    row.windows = requirementWindows(published, row.itemKey);
    row.vigenciaInicial = row.windows[0]?.from ?? null;
    row.vigenciaFinal = row.windows[row.windows.length - 1]?.to ?? null;
    row.situation = row.windows.some(
      (w) => w.from <= referencePeriod &&
        (w.to === null || w.to >= referencePeriod),
    )
      ? "vigente"
      : row.windows.length === 0 ||
          row.windows[0].from > referencePeriod
        ? "futuro"
        : "encerrado";
    row.pendingInDraft = pending.some((v) =>
      v.items.some((item) => item.item_key === row.itemKey),
    );
  }
  return [...rows.values()].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
}

/* ------------------------------------------------------------------ */
/* Plano de publicação — passos idempotentes por boundary.               */
/* ------------------------------------------------------------------ */

export type DocumentFormPayload = {
  itemKey: string;
  name: string;
  purpose: string | null;
  originKind: DraftItemInput["origin_kind"];
  recipientArea: DraftItemInput["recipient_area"];
  applicability: DraftItemInput["applicability"];
  sheet: DraftItemInput["sheet"];
  branchScope: DraftItemInput["branch_scope"];
  totvsReportRef: string | null;
  requirementNotes: string | null;
  validationScope: DraftItemInput["validation_scope"];
};

export type PublishStep = {
  /** Competência `effective_from_period` da versão a publicar. */
  effectiveFrom: string;
  /** Conjunto COMPLETO de itens da versão alvo. */
  items: DraftItemInput[];
};

function documentItem(
  payload: DocumentFormPayload,
  sortOrder: number | null,
): DraftItemInput {
  return {
    item_key: payload.itemKey,
    sort_order: sortOrder,
    sheet: payload.sheet,
    name: payload.name,
    purpose: payload.purpose,
    origin_kind: payload.originKind,
    recipient_area: payload.recipientArea,
    applicability: payload.applicability,
    branch_scope: payload.branchScope,
    totvs_report_ref: payload.totvsReportRef,
    requirement_notes: payload.requirementNotes,
    validation_scope: payload.validationScope,
  };
}

/** `base + item` (substitui mesma chave; preserva sort_order existente). */
function mergeItem(
  base: ChecklistTemplateItem[],
  payload: DocumentFormPayload,
): DraftItemInput[] {
  const items = toDraftItems(base);
  const index = items.findIndex(
    (entry) => entry.item_key === payload.itemKey,
  );
  const sortOrder =
    index >= 0
      ? (items[index].sort_order ?? null)
      : Math.max(0, ...items.map((i) => i.sort_order ?? 0)) + 10;
  const next = documentItem(payload, sortOrder);
  if (index >= 0) items[index] = next;
  else items.push(next);
  return items;
}

/**
 * Plano completo de publicação para a exigência de `item` na janela
 * [`effectiveFrom`, `effectiveUntil`] (sem término quando `until` = null):
 *
 * - Para cada boundary `b` com `from <= b <= until (ou ∞)`: publicar
 *   `winner@b + item` — propagação necessária porque versões são
 *   conjuntos absolutos (sem isso, a exigência morreria no próximo
 *   boundary já publicado).
 * - Com `until`: publicar em `nextPeriod(until)` o conteúdo
 *   `winner@(until+1) − item` calculado sobre a timeline ORIGINAL.
 * - Passos cujo alvo já é a configuração vigente no boundary são
 *   omitidos — o plano é naturalmente idempotente (retry converge).
 *
 * O cálculo é PURO sobre a lista fresca de versões — determinístico e
 * testável sem backend.
 */
export function planDocumentSave(
  versions: VersionWithItems[],
  document: DocumentFormPayload,
  effectiveFrom: string,
  effectiveUntil: string | null,
): PublishStep[] {
  const published = sortPublished(versions);
  const steps: PublishStep[] = [];
  const boundaries = timelineBoundaries(published).filter(
    (b) => b >= effectiveFrom,
  );
  const limit = effectiveUntil ?? "9999-12";
  const targets = new Set(
    [effectiveFrom, ...boundaries].filter((b) => b <= limit),
  );
  for (const boundary of [...targets].sort()) {
    const winner = winnerAt(published, boundary);
    const target = mergeItem(winner?.items ?? [], document);
    if (!itemsEqual(target, winner?.items ?? [])) {
      steps.push({ effectiveFrom: boundary, items: target });
    }
  }
  if (effectiveUntil) {
    const at = nextPeriod(effectiveUntil);
    const winner = winnerAt(published, at);
    const target = toDraftItems(winner?.items ?? []).filter(
      (item) => item.item_key !== document.itemKey,
    );
    // Estado efetivo em `at` APÓS as inserções do plano: a última versão
    // inserida com eff ≤ at passa a vencer — é ela que a remoção precisa
    // superar (senão a exigência propagada viveria indefinidamente).
    const lastInsert = steps[steps.length - 1];
    const currentEffective = lastInsert
      ? lastInsert.items
      : (winner?.items ?? []);
    if (!itemsEqual(target, currentEffective)) {
      steps.push({ effectiveFrom: at, items: target });
    }
  }
  return steps;
}

/* ------------------------------------------------------------------ */
/* Execução do plano — uma versão por vez, com resume por conteúdo.      */
/* ------------------------------------------------------------------ */

/**
 * Garante uma versão PUBLISHED com `eff` e `items` exatos:
 * 1. boundary já coberto por versão PUBLISHED igual → no-op;
 * 2. DRAFT/REVIEW aberto com itens iguais → retoma o ciclo (resume);
 * 3. caso contrário → ciclo completo DRAFT→update→REVIEW→PUBLISHED.
 *
 * `openVersions` = versões DRAFT/REVIEW com detalhe já carregado.
 */
async function ensurePublishedVersion(
  templateId: string,
  effectiveFrom: string,
  items: DraftItemInput[],
  openVersions: ChecklistTemplateVersionDetail[],
): Promise<void> {
  const reusable = openVersions.find(
    (version) => itemsEqual(version.items, items),
  );
  if (reusable) {
    if (reusable.status === "DRAFT") {
      await submitVersionForReview(templateId, reusable.version);
    }
    await publishTemplateVersion(templateId, reusable.version, {
      effective_from_period: effectiveFrom,
    });
    return;
  }
  if (openVersions.length > 0) {
    // Rascunho/revisão aberto com conteúdo diferente — nunca pisamos
    // trabalho de outro administrador nem de um rascunho divergente.
    throw new CatalogSaveError(
      "catalog_draft_conflict",
      "Existe uma versão em rascunho ou revisão com outro conteúdo — conclua-a ou descarte-a na Administração do checklist antes de salvar.",
    );
  }
  const draft = await createTemplateDraft(templateId);
  await updateTemplateDraft(templateId, draft.version, {
    revision: draft.revision,
    items,
  });
  await submitVersionForReview(templateId, draft.version);
  await publishTemplateVersion(templateId, draft.version, {
    effective_from_period: effectiveFrom,
  });
}

async function fetchVersionsWithItems(
  templateId: string,
): Promise<VersionWithItems[]> {
  const versionList = await listTemplateVersions(templateId);
  return Promise.all(
    versionList.map((version) =>
      getTemplateVersion(templateId, version.version),
    ),
  );
}

/**
 * Persiste a configuração de um documento com integridade de vigência:
 * o item é propagado a todos os boundaries cobertos pela janela e a
 * remoção é publicada em `until+1` quando houver término. Cada passo é
 * uma versão atômica do contrato; a sequência é idempotente — retry
 * após falha converge sem duplicar versões.
 */
export async function saveDocumentConfig(
  templateId: string,
  document: DocumentFormPayload,
  effectiveFrom: string,
  effectiveUntil: string | null,
): Promise<void> {
  const versions = await fetchVersionsWithItems(templateId);
  const steps = planDocumentSave(
    versions,
    document,
    effectiveFrom,
    effectiveUntil,
  );
  if (steps.length === 0) return;
  const open = versions.filter(
    (v) => v.status === "DRAFT" || v.status === "REVIEW",
  );
  for (const step of steps) {
    await ensurePublishedVersion(
      templateId,
      step.effectiveFrom,
      step.items,
      open,
    );
    // O passo consumiu ou criou uma versão — recalcular o estado aberto
    // exigiria nova consulta; como o plano é sequencial e um rascunho
    // usado vira PUBLISHED, limpamos a lista após o primeiro reuso.
    open.length = 0;
  }
}

/**
 * Publica somente a remoção do item a partir de `nextPeriod(untilPeriod)`
 * — usado por «Encerrar exigência» quando a configuração não muda.
 * A remoção é calculada sobre o vencedor real de `until+1` e propagada
 * — igualmente idempotente (boundary já sem o item → no-op).
 */
export async function publishRemovalVersion(
  templateId: string,
  itemKey: string,
  untilPeriod: string,
): Promise<void> {
  const versions = await fetchVersionsWithItems(templateId);
  const published = sortPublished(versions);
  const at = nextPeriod(untilPeriod);
  const winner = winnerAt(published, at);
  const target = toDraftItems(winner?.items ?? []).filter(
    (item) => item.item_key !== itemKey,
  );
  // O backend exige ≥1 item por versão — encerrar o único documento do
  // checklist não é representável sem contrato novo (DECISION_REQUIRED).
  if ((winner?.items.length ?? 0) > 0 && target.length === 0) {
    throw new CatalogSaveError(
      "catalog_last_item_end",
      "Não é possível encerrar o único documento do checklist.",
    );
  }
  if (itemsEqual(target, winner?.items ?? [])) return;
  const open = versions.filter(
    (v) => v.status === "DRAFT" || v.status === "REVIEW",
  );
  await ensurePublishedVersion(templateId, at, target, open);
}
