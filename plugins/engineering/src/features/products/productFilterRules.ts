/** Modelo de critérios dos filtros avançados do catálogo — lógica pura
 * de mapeamento entre o estado canônico da URL (`ProductsListUrlState`)
 * e as regras FIELD + OPERATOR + VALUE do painel. Cada campo expõe
 * somente o operador que o contrato oficial da Engineering API
 * realmente suporta:
 *   code/customer_reference → prefixo (`LIKE 'x%'`)  → "começa com"
 *   description             → matching textual        → "contém"
 *   groups/product_type     → IN (...)                → "é um de"
 *   subgroup                → igualdade exata         → "é igual a"
 * Nenhum critério filtra só a página carregada; tudo vai ao backend. */

import type { ProductsListUrlState } from "./productRoutes";

export type ProductFilterField =
  | "code"
  | "description"
  | "groups"
  | "types"
  | "customer_reference"
  | "subgroup";

export type ProductFilterRule = {
  field: ProductFilterField;
  /** Valor textual (operadores single-value). */
  text: string;
  /** Valores selecionados (operador "é um de"). */
  values: string[];
};

export type FieldKind = "text" | "multi";

export const FIELD_ORDER: readonly ProductFilterField[] = [
  "code",
  "description",
  "groups",
  "types",
  "customer_reference",
  "subgroup",
];

export const FIELD_META: Record<
  ProductFilterField,
  { label: string; operator: string; kind: FieldKind; placeholder: string }
> = {
  code: {
    label: "Código",
    operator: "começa com",
    kind: "text",
    placeholder: "Ex.: 100",
  },
  description: {
    label: "Descrição",
    operator: "contém",
    kind: "text",
    placeholder: "Ex.: CABO",
  },
  groups: {
    label: "Grupo",
    operator: "é um de",
    kind: "multi",
    placeholder: "",
  },
  types: {
    label: "Tipo",
    operator: "é um de",
    kind: "multi",
    placeholder: "",
  },
  customer_reference: {
    label: "Ref. cliente",
    operator: "começa com",
    kind: "text",
    placeholder: "Ex.: REF-",
  },
  subgroup: {
    label: "Subgrupo",
    operator: "é igual a",
    kind: "text",
    placeholder: "Ex.: 01",
  },
};

export type SelectOption = { value: string; label: string };

/** Estado canônico aplicado → critérios do painel (uma regra por campo
 * preenchido; campos vazios não geram critério). */
export function rulesFromListState(
  state: ProductsListUrlState,
): ProductFilterRule[] {
  const rules: ProductFilterRule[] = [];
  if (state.code.trim()) {
    rules.push({ field: "code", text: state.code, values: [] });
  }
  if (state.description.trim()) {
    rules.push({ field: "description", text: state.description, values: [] });
  }
  if (state.groups.length) {
    rules.push({ field: "groups", text: "", values: [...state.groups] });
  }
  if (state.types.length) {
    rules.push({ field: "types", text: "", values: [...state.types] });
  }
  if (state.customer_reference.trim()) {
    rules.push({
      field: "customer_reference",
      text: state.customer_reference,
      values: [],
    });
  }
  if (state.subgroup.trim()) {
    rules.push({ field: "subgroup", text: state.subgroup, values: [] });
  }
  return rules;
}

/** Critérios → estado canônico. Campos sem critério ficam vazios;
 * sort/page são preservados pelo chamador. */
export function applyRulesToListState(
  state: ProductsListUrlState,
  rules: ProductFilterRule[],
): ProductsListUrlState {
  const next: ProductsListUrlState = {
    ...state,
    code: "",
    description: "",
    customer_reference: "",
    subgroup: "",
    groups: [],
    types: [],
  };
  for (const rule of rules) {
    switch (rule.field) {
      case "code":
        next.code = rule.text.trim();
        break;
      case "description":
        next.description = rule.text.trim();
        break;
      case "customer_reference":
        next.customer_reference = rule.text.trim();
        break;
      case "subgroup":
        next.subgroup = rule.text.trim();
        break;
      case "groups":
        next.groups = [...rule.values];
        break;
      case "types":
        next.types = [...rule.values];
        break;
    }
  }
  return next;
}

/** Primeiro campo ainda não usado por outro critério (ordem do
 * catálogo) — evita regras duplicadas do mesmo campo. */
export function firstAvailableField(
  rules: ProductFilterRule[],
): ProductFilterField {
  const used = new Set(rules.map((rule) => rule.field));
  return FIELD_ORDER.find((field) => !used.has(field)) ?? "code";
}

/** Critério válido para consulta: texto preenchido ou ao menos um
 * valor selecionado — linhas vazias nunca viram filtro. */
export function isValidRule(rule: ProductFilterRule): boolean {
  return FIELD_META[rule.field].kind === "multi"
    ? rule.values.length > 0
    : rule.text.trim().length > 0;
}
