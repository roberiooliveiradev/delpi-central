/** Atalhos com `{{campo}}` exigem preenchimento antes de enviar a mensagem. */

export const SHORTCUT_PLACEHOLDER_PATTERN = /\{\{([a-zA-Z][a-zA-Z0-9]*)\}\}/g;

export type ShortcutFieldId =
  | "productCode"
  | "searchQuery"
  | "period"
  | "productDescription"
  | "salesOrder"
  | "ovNumber";

export type ShortcutFieldDefinition = {
  id: ShortcutFieldId;
  label: string;
  placeholder: string;
  inputMode?: "text" | "numeric";
  required?: boolean;
  pattern?: RegExp;
  patternHint?: string;
};

const FIELD_DEFINITIONS: Record<ShortcutFieldId, ShortcutFieldDefinition> = {
  productCode: {
    id: "productCode",
    label: "Código do produto",
    placeholder: "Ex.: 10080001",
    inputMode: "numeric",
    pattern: /^\d{5,9}$/,
    patternHint: "Informe um código numérico (5 a 9 dígitos).",
  },
  searchQuery: {
    id: "searchQuery",
    label: "O que pesquisar",
    placeholder: "Ex.: manual WEG CFW500",
    required: true,
  },
  period: {
    id: "period",
    label: "Período",
    placeholder: "Ex.: últimos 30 dias",
    required: true,
  },
  productDescription: {
    id: "productDescription",
    label: "Descrição ou termos",
    placeholder: "Ex.: cabo flexível 2,5 mm",
    required: true,
  },
  salesOrder: {
    id: "salesOrder",
    label: "Número da OV",
    placeholder: "Ex.: 123456",
    inputMode: "numeric",
    pattern: /^\d{4,12}$/,
    patternHint: "Informe o número da ordem de venda.",
  },
  ovNumber: {
    id: "ovNumber",
    label: "Número da OV",
    placeholder: "Ex.: 123456",
    inputMode: "numeric",
    pattern: /^\d{4,12}$/,
    patternHint: "Informe o número da ordem de venda.",
  },
};

export function hasShortcutPlaceholders(query: string): boolean {
  SHORTCUT_PLACEHOLDER_PATTERN.lastIndex = 0;
  return SHORTCUT_PLACEHOLDER_PATTERN.test(query.trim());
}

export function listShortcutFieldIds(query: string): ShortcutFieldId[] {
  const ids: ShortcutFieldId[] = [];
  const seen = new Set<string>();

  for (const match of query.matchAll(SHORTCUT_PLACEHOLDER_PATTERN)) {
    const raw = match[1];

    if (!raw || seen.has(raw)) {
      continue;
    }

    if (raw in FIELD_DEFINITIONS) {
      seen.add(raw);
      ids.push(raw as ShortcutFieldId);
    }
  }

  return ids;
}

export function resolveShortcutFields(query: string): ShortcutFieldDefinition[] {
  return listShortcutFieldIds(query).map((id) => FIELD_DEFINITIONS[id]);
}

export function fillShortcutTemplate(
  template: string,
  values: Record<string, string>,
): string {
  return template.replace(SHORTCUT_PLACEHOLDER_PATTERN, (_match, fieldId: string) => {
    const value = String(values[fieldId] ?? "").trim();
    return value;
  });
}

export function validateShortcutValues(
  fields: ShortcutFieldDefinition[],
  values: Record<string, string>,
): Record<string, string> | null {
  const errors: Record<string, string> = {};

  for (const field of fields) {
    const value = String(values[field.id] ?? "").trim();

    if ((field.required ?? true) && !value) {
      errors[field.id] = "Preencha este campo.";
      continue;
    }

    if (value && field.pattern && !field.pattern.test(value)) {
      errors[field.id] = field.patternHint ?? "Valor inválido.";
    }
  }

  return Object.keys(errors).length > 0 ? errors : null;
}

/** Legado `{product_code}` / `{query}` do playbook → placeholders do MFE. */
export function normalizeShortcutTemplate(query: string): string {
  return query
    .replace(/\{product_code\}/gi, "{{productCode}}")
    .replace(/\{query\}/gi, "{{searchQuery}}")
    .replace(/\{topic\}/gi, "{{searchQuery}}")
    .trim();
}

export type ShortcutPrefillContext = {
  productCode?: string | null;
  searchQuery?: string | null;
};

export function buildShortcutPrefill(
  fieldIds: ShortcutFieldId[],
  context: ShortcutPrefillContext = {},
): Record<string, string> {
  const values: Record<string, string> = {};

  for (const fieldId of fieldIds) {
    if (fieldId === "productCode" && context.productCode) {
      values.productCode = context.productCode;
    }

    if (fieldId === "searchQuery" && context.searchQuery) {
      values.searchQuery = context.searchQuery;
    }
  }

  return values;
}

export function extractProductCodeFromContextChips(
  chips: Array<{ kind?: string; value?: string }>,
): string | null {
  for (const chip of chips) {
    if (chip.kind !== "product") {
      continue;
    }

    const normalized = String(chip.value ?? "").replace(/\./g, "").trim();

    if (/^\d{5,9}$/.test(normalized)) {
      return normalized;
    }
  }

  return null;
}
