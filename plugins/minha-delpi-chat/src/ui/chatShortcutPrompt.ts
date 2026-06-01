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
  | "ovNumber"
  | "emailRecipient"
  | "emailSubject"
  | "textContent"
  | "meetingNotes"
  | "announcementTopic";

/** Exemplo padrão no campo e na prévia de atalhos com `{{searchQuery}}`. */
export const SEARCH_QUERY_PLACEHOLDER = "Ex.: DELPI Conexões Elétricas";

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
    placeholder: SEARCH_QUERY_PLACEHOLDER,
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
    placeholder: "Ex.: 003267",
    inputMode: "numeric",
    pattern: /^\d{4,12}$/,
    patternHint: "Informe o número da ordem de venda.",
  },
  ovNumber: {
    id: "ovNumber",
    label: "Número da OV",
    placeholder: "Ex.: 003267",
    inputMode: "numeric",
    pattern: /^\d{4,12}$/,
    patternHint: "Informe o número da ordem de venda.",
  },
  emailRecipient: {
    id: "emailRecipient",
    label: "Destinatário",
    placeholder: "Ex.: fornecedor ABC",
    required: true,
  },
  emailSubject: {
    id: "emailSubject",
    label: "Assunto do e-mail",
    placeholder: "Ex.: prazo de entrega",
    required: true,
  },
  textContent: {
    id: "textContent",
    label: "Texto para revisar",
    placeholder: "Cole ou descreva o trecho com erros",
    required: true,
  },
  meetingNotes: {
    id: "meetingNotes",
    label: "Notas da reunião",
    placeholder: "Cole as anotações ou tópicos discutidos",
    required: true,
  },
  announcementTopic: {
    id: "announcementTopic",
    label: "Assunto do comunicado",
    placeholder: "Ex.: prazo de entrega",
    required: true,
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

/** Template padrão ao clicar em novidades/atalho de pesquisa web. */
export const WEB_SEARCH_STARTER_QUERY = "pesquise na web sobre {{searchQuery}}";

/** Novo pedido de pesquisa web — não chips de follow-up (“fontes da pesquisa web acima”). */
export function isWebSearchStarterQuery(query: string): boolean {
  const normalized = normalizeShortcutTemplate(query.trim());

  if (normalized.includes("{{searchQuery}}")) {
    return true;
  }

  return /^(pesquise|busque)\s+(na\s+)?(web|internet|online)\s+sobre\b/i.test(normalized);
}

export type StarterInvokeContext = {
  featureId?: string | null;
  starterId?: string | null;
};

export function resolveStarterQueryForFeature(
  query: string | null | undefined,
  context: StarterInvokeContext = {},
): string | null {
  if (context.featureId === "web_search") {
    return WEB_SEARCH_STARTER_QUERY;
  }

  const trimmed = String(query ?? "").trim();

  return trimmed || null;
}

const PRODUCT_STARTER_IDS = new Set([
  "product",
  "stock",
  "supplier",
  "structure",
  "sales",
  "purchases",
]);

/** Indica se o clique no card da home deve abrir o diálogo de preenchimento. */
export function starterRequiresShortcutModal(
  query: string,
  context: StarterInvokeContext = {},
): boolean {
  const normalized = normalizeShortcutTemplate(query.trim());

  if (!normalized) {
    return false;
  }

  if (context.featureId === "web_search") {
    return hasShortcutPlaceholders(normalized);
  }

  if (isWebSearchStarterQuery(normalized)) {
    return hasShortcutPlaceholders(normalized);
  }

  return hasShortcutPlaceholders(normalized);
}

/** Diálogo adequado ao tipo de atalho (produto, web, textos administrativos). */
export function resolveStarterPromptOptions(
  query: string,
  context: StarterInvokeContext = {},
): (typeof CHAT_SHORTCUT_PROMPT_COPY)[keyof typeof CHAT_SHORTCUT_PROMPT_COPY] {
  const normalized = normalizeShortcutTemplate(query.trim());

  if (
    context.featureId === "web_search" ||
    (isWebSearchStarterQuery(normalized) && hasShortcutPlaceholders(normalized))
  ) {
    return CHAT_SHORTCUT_PROMPT_COPY.webSearch;
  }

  const starterId = String(context.starterId ?? "").trim().toLowerCase();

  if (starterId === "email") {
    return CHAT_SHORTCUT_PROMPT_COPY.textEmail;
  }

  if (starterId === "correct" || starterId === "text") {
    return CHAT_SHORTCUT_PROMPT_COPY.textCorrect;
  }

  if (starterId === "minutes") {
    return CHAT_SHORTCUT_PROMPT_COPY.textMinutes;
  }

  if (PRODUCT_STARTER_IDS.has(starterId) || normalized.includes("{{productCode}}")) {
    return CHAT_SHORTCUT_PROMPT_COPY.product;
  }

  if (hasShortcutPlaceholders(normalized)) {
    return CHAT_SHORTCUT_PROMPT_COPY.generic;
  }

  return CHAT_SHORTCUT_PROMPT_COPY.send;
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
  webSearch: {
    title: "Pesquisa na web",
    description: "Informe o assunto que deseja buscar na internet pública.",
    confirmLabel: "Pesquisar",
  },
  product: {
    title: "Consulta operacional",
    description: "Informe o código do produto ou os dados solicitados.",
    confirmLabel: "Enviar pergunta",
  },
  textEmail: {
    title: "E-mail formal",
    description: "Informe o destinatário e o assunto antes de gerar o texto.",
    confirmLabel: "Enviar",
  },
  textCorrect: {
    title: "Revisar texto",
    description: "Cole ou descreva o trecho que deseja corrigir.",
    confirmLabel: "Enviar",
  },
  textMinutes: {
    title: "Ata de reunião",
    description: "Informe as notas ou tópicos para montar a ata.",
    confirmLabel: "Enviar",
  },
  generic: {
    title: "Preencha para continuar",
    description: "Complete os campos para montar a solicitação ao agente.",
    confirmLabel: "Enviar pergunta",
  },
} as const;
