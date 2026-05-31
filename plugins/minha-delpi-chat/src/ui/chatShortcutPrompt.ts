/** Atalhos com `{{campo}}` exigem preenchimento antes de enviar a mensagem. */

const SHORTCUT_PLACEHOLDER_SOURCE = String.raw`\{\{([a-zA-Z][a-zA-Z0-9]*)\}\}`;

/** Sem flag `g` — seguro para `.test()` sem corromper `lastIndex` de outras chamadas. */
const SHORTCUT_PLACEHOLDER_DETECT = new RegExp(SHORTCUT_PLACEHOLDER_SOURCE);

/** Com flag `g` — usar só em `matchAll` / `replace` após `lastIndex = 0`. */
export const SHORTCUT_PLACEHOLDER_PATTERN = new RegExp(SHORTCUT_PLACEHOLDER_SOURCE, "g");

export type ShortcutFieldId =
  | "productCode"
  | "searchQuery"
  | "period"
  | "productDescription"
  | "salesOrder"
  | "ovNumber";

export type ShortcutFieldDefinition = {
  id: string;
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
    pattern: /^\d{4,12}$/,
    patternHint: "Informe um código numérico (4 a 12 dígitos).",
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
  return SHORTCUT_PLACEHOLDER_DETECT.test(query.trim());
}

export function listShortcutFieldIds(query: string): string[] {
  const ids: string[] = [];
  const seen = new Set<string>();

  SHORTCUT_PLACEHOLDER_PATTERN.lastIndex = 0;

  for (const match of query.matchAll(SHORTCUT_PLACEHOLDER_PATTERN)) {
    const raw = match[1];

    if (!raw || seen.has(raw)) {
      continue;
    }

    seen.add(raw);
    ids.push(raw);
  }

  return ids;
}

function placeholderLabel(fieldId: string): string {
  if (fieldId in FIELD_DEFINITIONS) {
    return FIELD_DEFINITIONS[fieldId as ShortcutFieldId].label;
  }

  const spaced = fieldId.replace(/([A-Z])/g, " $1").trim();

  return spaced ? spaced.charAt(0).toUpperCase() + spaced.slice(1) : "Valor";
}

/** Texto de exemplo exibido no lugar de `{{campo}}` (cards, tour, tooltips). */
export function shortcutDisplayHintForField(fieldId: string): string {
  if (fieldId in FIELD_DEFINITIONS) {
    return FIELD_DEFINITIONS[fieldId as ShortcutFieldId].placeholder;
  }

  return `informe ${placeholderLabel(fieldId).toLowerCase()}`;
}

/**
 * Versão legível de templates com placeholders — não altera o valor enviado ao clicar.
 * Ex.: `me fale do produto {{productCode}}` → `me fale do produto Ex.: 10080001`
 */
export function formatShortcutTemplateForDisplay(template: string): string {
  const normalized = normalizeShortcutTemplate(template);

  if (!hasShortcutPlaceholders(normalized)) {
    return normalized;
  }

  SHORTCUT_PLACEHOLDER_PATTERN.lastIndex = 0;

  return normalized.replace(SHORTCUT_PLACEHOLDER_PATTERN, (_match, fieldId: string) =>
    shortcutDisplayHintForField(fieldId),
  );
}

function fieldDefinitionForPlaceholder(fieldId: string): ShortcutFieldDefinition {
  if (fieldId in FIELD_DEFINITIONS) {
    return FIELD_DEFINITIONS[fieldId as ShortcutFieldId];
  }

  const label = placeholderLabel(fieldId);

  return {
    id: fieldId,
    label,
    placeholder: `Informe ${label.toLowerCase()}`,
    required: true,
  };
}

export function resolveShortcutFields(query: string): ShortcutFieldDefinition[] {
  return listShortcutFieldIds(query).map((id) => fieldDefinitionForPlaceholder(id));
}

/** Bloqueia envio se ainda houver `{{campo}}` sem substituir. */
export function hasUnresolvedShortcutPlaceholders(query: string): boolean {
  return SHORTCUT_PLACEHOLDER_DETECT.test(query.trim());
}

export function fillShortcutTemplate(
  template: string,
  values: Record<string, string>,
): string {
  SHORTCUT_PLACEHOLDER_PATTERN.lastIndex = 0;

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
  fieldIds: string[],
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

    if (/^\d{4,12}$/.test(normalized)) {
      return normalized;
    }
  }

  return null;
}

/** Textos do diálogo de atalhos — linguagem para o usuário final (sem «composer»). */
export const CHAT_SHORTCUT_PROMPT_COPY = {
  /** Coloca a pergunta no campo de mensagem; o usuário revisa e envia. */
  insert: {
    title: "Preencha para continuar",
    description:
      "A pergunta montada aparecerá no campo de mensagem abaixo. Revise e envie quando estiver pronta.",
    confirmLabel: "Inserir pergunta",
  },
  /** Envia direto após preencher (ex.: ajuda / experimentar). */
  send: {
    title: "Preencha para continuar",
    description: "Informe os dados para enviar a pergunta ao agente.",
    confirmLabel: "Enviar pergunta",
  },
  /** Reutilizar mensagem do histórico no campo de mensagem. */
  reuse: {
    title: "Preencha para continuar",
    description:
      "Complete os campos. A mensagem montada voltará ao campo de mensagem para você revisar.",
    confirmLabel: "Inserir pergunta",
  },
  resend: {
    title: "Preencha para continuar",
    description: "Informe os dados antes de reenviar a mensagem.",
    confirmLabel: "Reenviar",
  },
} as const;
