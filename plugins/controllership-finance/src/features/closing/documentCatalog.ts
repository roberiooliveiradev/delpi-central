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
  saveDocumentRequirement,
  type ChecklistTemplateItem,
  type ChecklistTemplateVersion,
  type DocumentRequirementResult,
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

/** MAX(version) da timeline — revisão do catálogo para o OCC da BFF. */
export function catalogBaseVersion(
  versions: ChecklistTemplateVersion[],
): number {
  return versions.reduce(
    (max, version) => Math.max(max, version.version),
    0,
  );
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

export type RequirementSaveOptions = {
  /** OCC obrigatório — MAX(version) visto pelo cliente (PO D5). */
  baseVersion: number;
  /** Chave única por intenção do usuário — retry reutiliza a mesma. */
  idempotencyKey: string;
  /** Intenção explícita de deixar o checklist sem exigências (DR-2). */
  allowEmpty?: boolean;
};

function toApiItem(document: DocumentFormPayload): DraftItemInput {
  return {
    item_key: document.itemKey,
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
}

/**
 * DR-1 — grava a configuração de um documento em UMA chamada
 * transacional da BFF: inclusão/edição/término/reativação propagados a
 * todos os boundaries cobertos pela janela, atomicamente. O backend é
 * a autoridade de publicação; o MFE não orquestra mais versões.
 */
export function saveDocumentConfig(
  templateId: string,
  document: DocumentFormPayload,
  effectiveFrom: string,
  effectiveUntil: string | null,
  options: RequirementSaveOptions,
): Promise<DocumentRequirementResult> {
  return saveDocumentRequirement(
    templateId,
    document.itemKey,
    {
      item: toApiItem(document),
      effective_from: effectiveFrom,
      effective_until: effectiveUntil,
      base_version: options.baseVersion,
      allow_empty: options.allowEmpty ?? false,
    },
    options.idempotencyKey,
  );
}

/**
 * Encerra a exigência do documento a partir de `effectiveFrom` — o
 * mesmo comando transacional com `item` omitido. Quando o documento é
 * a última exigência, a BFF exige `allowEmpty` explícito (DR-2) — a
 * página confirma com o usuário antes de reenviar.
 */
export function endDocumentRequirement(
  templateId: string,
  itemKey: string,
  effectiveFrom: string,
  options: RequirementSaveOptions,
): Promise<DocumentRequirementResult> {
  return saveDocumentRequirement(
    templateId,
    itemKey,
    {
      effective_from: effectiveFrom,
      base_version: options.baseVersion,
      allow_empty: options.allowEmpty ?? false,
    },
    options.idempotencyKey,
  );
}
