import type { Criterion } from "../api/audit5sApi";

export type EditableCriterion = {
  clientId: string;
  senso_order: number;
  sort_order: number;
  code: string;
  description: string;
};

export type CatalogDiff = {
  added: number;
  edited: number;
  removed: number;
  hasChanges: boolean;
};

const SENSO_CODE_PREFIX: Record<number, string> = {
  1: "U",
  2: "O",
  3: "L",
  4: "P",
  5: "D",
};

function normalizeDescription(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function criterionKey(item: Pick<EditableCriterion, "senso_order" | "sort_order" | "code">) {
  return `${item.senso_order}:${item.sort_order}:${item.code.toUpperCase()}`;
}

export function createClientId(): string {
  return `tmp-${crypto.randomUUID()}`;
}

export function criteriaFromCatalog(criteria: Criterion[]): EditableCriterion[] {
  return criteria.map((item) => ({
    clientId: item.id,
    senso_order: item.senso_order,
    sort_order: item.sort_order,
    code: item.code,
    description: item.description,
  }));
}

export function groupCriteriaBySenso(
  criteria: EditableCriterion[],
): Map<number, EditableCriterion[]> {
  const grouped = new Map<number, EditableCriterion[]>();
  for (const order of [1, 2, 3, 4, 5]) {
    grouped.set(
      order,
      criteria
        .filter((item) => item.senso_order === order)
        .sort((a, b) => a.sort_order - b.sort_order),
    );
  }
  return grouped;
}

export function resolveSensoName(
  sensoOrder: number,
  criteria: Criterion[],
  sensoNames: Array<{ senso_sort_order: number; name: string }>,
): string {
  const override = sensoNames.find((item) => item.senso_sort_order === sensoOrder);
  if (override) return override.name;
  const fromCriteria = criteria.find((item) => item.senso_order === sensoOrder);
  return fromCriteria?.senso_name ?? `Senso ${sensoOrder}`;
}

export function suggestCriterionCode(
  sensoOrder: number,
  criteria: EditableCriterion[],
): string {
  const prefix = SENSO_CODE_PREFIX[sensoOrder] ?? "X";
  const used = new Set(
    criteria
      .filter((item) => item.senso_order === sensoOrder)
      .map((item) => item.code.toUpperCase()),
  );
  for (let index = 1; index <= 99; index += 1) {
    const candidate = `${prefix}${String(index).padStart(2, "0")}`;
    if (!used.has(candidate)) {
      return candidate;
    }
  }
  return `${prefix}99`;
}

export function addCriterionToSenso(
  criteria: EditableCriterion[],
  sensoOrder: number,
): EditableCriterion[] {
  const sensoItems = criteria.filter((item) => item.senso_order === sensoOrder);
  const nextSortOrder =
    sensoItems.length === 0 ? 1 : Math.max(...sensoItems.map((item) => item.sort_order)) + 1;
  const draft = [...criteria];
  draft.push({
    clientId: createClientId(),
    senso_order: sensoOrder,
    sort_order: nextSortOrder,
    code: suggestCriterionCode(sensoOrder, draft),
    description: "",
  });
  return draft;
}

export function removeCriterion(
  criteria: EditableCriterion[],
  clientId: string,
): EditableCriterion[] {
  return criteria.filter((item) => item.clientId !== clientId);
}

export function updateCriterion(
  criteria: EditableCriterion[],
  clientId: string,
  patch: Partial<Pick<EditableCriterion, "code" | "description" | "sort_order">>,
): EditableCriterion[] {
  return criteria.map((item) =>
    item.clientId === clientId
      ? {
          ...item,
          ...patch,
          code: patch.code ? patch.code.toUpperCase() : item.code,
        }
      : item,
  );
}

export function buildPublishPayload(
  branch: string,
  criteria: EditableCriterion[],
): {
  branch_code: string;
  criteria: Array<{
    senso_order: number;
    sort_order: number;
    code: string;
    description: string;
  }>;
} {
  return {
    branch_code: branch,
    criteria: criteria.map((item) => ({
      senso_order: item.senso_order,
      sort_order: item.sort_order,
      code: item.code.trim().toUpperCase(),
      description: normalizeDescription(item.description),
    })),
  };
}

export function computeCatalogDiff(
  baseline: EditableCriterion[],
  draft: EditableCriterion[],
): CatalogDiff {
  const baselineByCode = new Map(baseline.map((item) => [item.code.toUpperCase(), item]));
  const draftByCode = new Map(draft.map((item) => [item.code.toUpperCase(), item]));

  let added = 0;
  let edited = 0;
  let removed = 0;

  for (const item of draft) {
    const previous = baselineByCode.get(item.code.toUpperCase());
    if (!previous) {
      added += 1;
      continue;
    }
    const samePosition =
      previous.senso_order === item.senso_order && previous.sort_order === item.sort_order;
    const sameDescription =
      normalizeDescription(previous.description) === normalizeDescription(item.description);
    if (!samePosition || !sameDescription) {
      edited += 1;
    }
  }

  for (const item of baseline) {
    if (!draftByCode.has(item.code.toUpperCase())) {
      removed += 1;
    }
  }

  return {
    added,
    edited,
    removed,
    hasChanges: added + edited + removed > 0,
  };
}

export function catalogsAreEquivalent(
  baseline: EditableCriterion[],
  draft: EditableCriterion[],
): boolean {
  if (baseline.length !== draft.length) return false;
  const baselineSnapshot = baseline
    .map((item) =>
      [
        item.senso_order,
        item.sort_order,
        item.code.toUpperCase(),
        normalizeDescription(item.description),
      ].join("|"),
    )
    .sort();
  const draftSnapshot = draft
    .map((item) =>
      [
        item.senso_order,
        item.sort_order,
        item.code.toUpperCase(),
        normalizeDescription(item.description),
      ].join("|"),
    )
    .sort();
  return baselineSnapshot.every((value, index) => value === draftSnapshot[index]);
}

export function validateDraftCriteria(criteria: EditableCriterion[]): string | null {
  if (criteria.length === 0) {
    return "Adicione ao menos um critério.";
  }

  const codes = new Set<string>();
  const positions = new Set<string>();
  const sensos = new Set<number>();

  for (const item of criteria) {
    const code = item.code.trim().toUpperCase();
    if (!/^[A-Z]\d{2}$/.test(code)) {
      return `Código inválido: ${code || "(vazio)"}.`;
    }
    if (normalizeDescription(item.description).length < 3) {
      return `Preencha a descrição do critério ${code}.`;
    }
    if (codes.has(code)) {
      return `Código duplicado: ${code}.`;
    }
    const position = criterionKey(item);
    if (positions.has(position)) {
      return `Ordem duplicada no senso ${item.senso_order}.`;
    }
    codes.add(code);
    positions.add(position);
    sensos.add(item.senso_order);
  }

  for (const order of [1, 2, 3, 4, 5]) {
    if (!sensos.has(order)) {
      return `O senso ${order} precisa de ao menos um critério.`;
    }
  }

  return null;
}
