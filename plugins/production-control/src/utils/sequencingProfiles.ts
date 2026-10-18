import type {
  SequencingCriterion,
  SequencingCriterionType,
  SequencingProfile,
  SequencingProfileStatus,
} from "../types";

/** Critérios opcionais do perfil — `pa_due_date` é sempre soberano e primeiro. */
export const OPTIONAL_CRITERIA: readonly SequencingCriterionType[] = [
  "tool_group",
  "material_code",
] as const;

/**
 * Grupos SB1 de cabos — mesmo conjunto usado no seed de homologação
 * («Corte e Decape - Entrega e Cabo»). Ponto de partida, editável.
 */
export const DEFAULT_CABLE_GROUPS: readonly string[] = [
  "1037",
  "1038",
  "1053",
  "1007",
  "1042",
  "1047",
  "1040",
  "1041",
  "1055",
  "1049",
  "1002",
  "1001",
  "1005",
  "1051",
  "1044",
  "1036",
] as const;

/** Parâmetros fixos do critério material_code — não inventar política nova. */
export function buildMaterialParams(groups: string[]): Record<string, unknown> {
  return {
    material_type: "MP",
    eligible_product_groups: groups,
    identity_source: "operation_then_order",
    ignore_zeroed_allocations: true,
    on_missing: "flag",
    on_ambiguous: "flag",
  };
}

/** Extrai os grupos configurados de um critério material_code existente. */
export function materialGroups(criterion: SequencingCriterion | undefined): string[] {
  const params = criterion?.params;
  if (!params || typeof params !== "object") return [];
  const groups = (params as Record<string, unknown>).eligible_product_groups;
  if (!Array.isArray(groups)) return [];
  return groups
    .map((item) => String(item ?? "").trim())
    .filter((item) => item.length > 0);
}

/**
 * Converte texto do usuário em lista de grupos SB1: separa por vírgula,
 * espaço ou quebra de linha; mantém somente dígitos e preserva zeros à
 * esquerda. Devolve também os trechos rejeitados para o aviso de validação.
 */
export function parseProductGroups(text: string): { groups: string[]; rejected: string[] } {
  const groups: string[] = [];
  const rejected: string[] = [];
  for (const raw of text.split(/[\s,;]+/)) {
    const token = raw.trim();
    if (!token) continue;
    if (/^\d+$/.test(token)) {
      if (!groups.includes(token)) groups.push(token);
    } else {
      rejected.push(token);
    }
  }
  return { groups, rejected };
}

export type CriteriaEditorItem = {
  type: SequencingCriterionType;
  groups: string[];
};

/** Estado inicial do editor a partir de um perfil existente (ou novo). */
export function criteriaFromProfile(profile: SequencingProfile | null): CriteriaEditorItem[] {
  const items: CriteriaEditorItem[] = [{ type: "pa_due_date", groups: [] }];
  for (const criterion of profile?.criteria ?? []) {
    if (criterion.type === "pa_due_date") continue;
    if (!OPTIONAL_CRITERIA.includes(criterion.type)) continue;
    items.push({
      type: criterion.type,
      groups: criterion.type === "material_code" ? materialGroups(criterion) : [],
    });
  }
  return items;
}

/** Monta o payload `criteria` na ordem do editor — pa_due_date primeiro. */
export function buildCriteriaPayload(items: CriteriaEditorItem[]): SequencingCriterion[] {
  return items.map((item) =>
    item.type === "material_code"
      ? { type: item.type, params: buildMaterialParams(item.groups) }
      : { type: item.type },
  );
}

/** Tipos opcionais ainda disponíveis para adicionar (sem duplicar critério). */
export function availableCriteria(items: CriteriaEditorItem[]): SequencingCriterionType[] {
  const used = new Set(items.map((item) => item.type));
  return OPTIONAL_CRITERIA.filter((type) => !used.has(type));
}

/** Move o item uma posição para cima/baixo — o primeiro nunca se move. */
export function moveCriterion(
  items: CriteriaEditorItem[],
  index: number,
  direction: -1 | 1,
): CriteriaEditorItem[] {
  const target = index + direction;
  if (index <= 0 || target <= 0 || target >= items.length) return items;
  const next = [...items];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

export function removeCriterion(
  items: CriteriaEditorItem[],
  index: number,
): CriteriaEditorItem[] {
  if (index <= 0) return items;
  return items.filter((_, itemIndex) => itemIndex !== index);
}

export function addCriterion(
  items: CriteriaEditorItem[],
  type: SequencingCriterionType,
): CriteriaEditorItem[] {
  if (type === "pa_due_date" || !availableCriteria(items).includes(type)) return items;
  return [
    ...items,
    { type, groups: type === "material_code" ? [...DEFAULT_CABLE_GROUPS] : [] },
  ];
}

/** Validação de tela — o backend continua sendo a autoridade final. */
export function validateCriteria(items: CriteriaEditorItem[]): string | null {
  if (items[0]?.type !== "pa_due_date") {
    return "A data de entrega precisa ser o primeiro critério.";
  }
  const types = items.map((item) => item.type);
  if (new Set(types).size !== types.length) {
    return "Não é possível repetir um critério.";
  }
  const material = items.find((item) => item.type === "material_code");
  if (material && material.groups.length === 0) {
    return "Informe ao menos um grupo de produto para o critério de material.";
  }
  return null;
}

export function statusLabel(status: SequencingProfileStatus): string {
  if (status === "active") return "Ativo";
  if (status === "draft") return "Rascunho";
  return "Arquivado";
}
