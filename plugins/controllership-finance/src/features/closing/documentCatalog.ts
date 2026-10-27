/**
 * Catálogo mestre de documentos do fechamento — UX-012.
 *
 * O contrato da BFF é versionado e atômico (`/admin/checklist-templates*`):
 * cada versão publicada define o conjunto completo de exigências a partir
 * de `effective_from_period`, e a vigência de cada tipo de documento é
 * DERIVADA da timeline de versões — um item é exigido nos períodos em que
 * a versão vencedora o contém.
 *
 * A experiência por documento (listar/criar/editar) orquestra o ciclo
 * DRAFT → REVIEW → PUBLISHED do contrato existente: nenhuma persistência
 * paralela, nenhum endpoint novo. Fechamentos encerrados nunca mudam —
 * o snapshot da competência é cópia congelada.
 */
import {
  createTemplateDraft,
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

/** Competência «AAAA-MM» → «MM/AAAA» para exibição. */
export function formatPeriod(period: string | null): string {
  if (!period) return "—";
  const [year, month] = period.split("-");
  return `${month}/${year}`;
}

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

/**
 * Janelas de exigência de um item: a versão vencedora em cada fronteira
 * da timeline decide se o item é exigido naquele intervalo.
 */
function requirementWindows(
  published: VersionWithItems[],
  itemKey: string,
): RequirementWindow[] {
  const sorted = [...published]
    .filter((v) => v.effective_from_period !== null)
    .sort((a, b) =>
      (a.effective_from_period ?? "").localeCompare(
        b.effective_from_period ?? "",
      ),
    );
  if (sorted.length === 0) return [];
  const boundaries = [
    ...new Set(
      sorted.map((v) => v.effective_from_period).filter(
        (p): p is string => p !== null,
      ),
    ),
  ].sort();
  const windows: RequirementWindow[] = [];
  let openFrom: string | null = null;
  boundaries.forEach((boundary, index) => {
    const winner = [...sorted]
      .reverse()
      .find(
        (v) => (v.effective_from_period ?? "") <= boundary,
      );
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
  const published = versions.filter((v) => v.status === "PUBLISHED");
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

async function publishItemsVersion(
  templateId: string,
  items: DraftItemInput[],
  effectiveFrom: string,
): Promise<ChecklistTemplateVersionDetail> {
  const draft = await createTemplateDraft(templateId);
  const updated = await updateTemplateDraft(
    templateId,
    draft.version,
    { revision: draft.revision, items },
  );
  await submitVersionForReview(templateId, draft.version);
  await publishTemplateVersion(templateId, draft.version, {
    effective_from_period: effectiveFrom,
  });
  return updated;
}

/**
 * Persiste a configuração de um documento: nova versão publicada a partir
 * de `effectiveFrom` com a configuração informada (inserção ou edição por
 * `item_key`), mais versão de remoção em `effectiveUntil + 1` quando houver
 * término. Fechamentos já abertos/encerrados não são reescritos — a
 * vigência é sempre prospectiva e atômica por versão.
 */
export async function saveDocumentConfig(
  templateId: string,
  baseItems: ChecklistTemplateItem[],
  document: DocumentFormPayload,
  effectiveFrom: string,
  effectiveUntil: string | null,
): Promise<void> {
  const items = toDraftItems(baseItems);
  const index = items.findIndex(
    (item) => item.item_key === document.itemKey,
  );
  const next: DraftItemInput = {
    item_key: document.itemKey,
    sort_order:
      index >= 0
        ? items[index].sort_order
        : (Math.max(0, ...items.map((i) => i.sort_order ?? 0)) + 10),
    sheet: document.sheet,
    name: document.name,
    purpose: document.purpose,
    origin_kind: document.originKind,
    recipient_area: document.recipientArea,
    applicability: document.applicability,
    branch_scope: document.branchScope,
    totvs_report_ref: document.totvsReportRef,
    requirement_notes: document.requirementNotes,
    validation_scope: document.validationScope,
  };
  if (index >= 0) items[index] = next;
  else items.push(next);
  await publishItemsVersion(templateId, items, effectiveFrom);
  if (effectiveUntil) {
    await publishRemovalVersion(
      templateId,
      items.filter((item) => item.item_key !== document.itemKey),
      effectiveUntil,
    );
  }
}

/**
 * Publica somente a remoção do item a partir de `nextPeriod(untilPeriod)` —
 * usado por «Encerrar exigência» quando a configuração não muda.
 */
export async function publishRemovalVersion(
  templateId: string,
  remainingItems: DraftItemInput[],
  untilPeriod: string,
): Promise<void> {
  // O backend exige ≥1 item por versão — encerrar o único documento
  // do checklist não é representável sem contrato novo.
  if (remainingItems.length === 0) {
    throw new CatalogSaveError(
      "catalog_last_item_end",
      "Não é possível encerrar o único documento do checklist.",
    );
  }
  await publishItemsVersion(
    templateId,
    remainingItems,
    nextPeriod(untilPeriod),
  );
}
