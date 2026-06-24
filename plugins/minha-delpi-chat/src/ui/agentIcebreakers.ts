import { DEFAULT_AGENT_ICEBREAKERS } from "./chatHomeStarters";
import {
  formatShortcutTemplateForDisplay,
  hasShortcutPlaceholders,
  ICEBREAKER_FIELD_TYPE_OPTIONS,
  listShortcutFieldIds,
  resolveShortcutFields,
  shortcutFillPromptForTemplate,
  type IcebreakerFieldConfig,
  type ShortcutFieldDefinition,
} from "./chatShortcutPrompt";

export type { IcebreakerFieldConfig };
export { ICEBREAKER_FIELD_TYPE_OPTIONS };

/** Limite por sugestão (caracteres) — sem teto de quantidade na home ou no builder. */
export const AGENT_ICEBREAKER_MAX_CHARS = 72;
export const AGENT_ICEBREAKER_TITLE_MAX_CHARS = 48;
export const AGENT_ICEBREAKER_HINT_MAX_CHARS = 96;
export const AGENT_ICEBREAKER_FIELD_ID_MAX_CHARS = 32;
export const AGENT_ICEBREAKER_FIELD_LABEL_MAX_CHARS = 48;

/** Entrada persistida em `metadata.icebreakers`. */
export type AgentIcebreakerEntry = {
  template: string;
  label?: string;
  hint?: string;
  fields?: IcebreakerFieldConfig[];
};

export type IcebreakerVisualKind =
  | "product"
  | "stock"
  | "web"
  | "capabilities"
  | "text"
  | "generic";

const DEFAULT_ICEBREAKER_CATALOG: AgentIcebreakerEntry[] = [
  {
    label: "Consultar produto",
    hint: "Cadastro, estoque e visão geral",
    template: "me fale do produto {{productCode}}",
    fields: [{ id: "productCode", label: "Código do produto", fieldType: "productCode" }],
  },
  {
    label: "Status fabril",
    hint: "Estrutura, MPs, produção e expedição",
    template: "qual o status fabril hoje do produto {{productCode}}?",
    fields: [{ id: "productCode", label: "Código do produto", fieldType: "productCode" }],
  },
  {
    label: "MPs exclusivas",
    hint: "Matérias-primas usadas só neste PA",
    template: "quais MPs exclusivas tem o produto {{productCode}}?",
    fields: [{ id: "productCode", label: "Código do produto", fieldType: "productCode" }],
  },
  {
    label: "Preço da MP",
    hint: "Fornecedor, ICMS, orçamento e variação",
    template: "análise de preço da matéria-prima {{productCode}}",
    fields: [{ id: "productCode", label: "Código da matéria-prima", fieldType: "productCode" }],
  },
  {
    label: "Impacto de custo",
    hint: "Ranking Pareto das MPs na BOM",
    template: "quais materiais mais impactam o custo do PA {{productCode}}?",
    fields: [{ id: "productCode", label: "Código do PA", fieldType: "productCode" }],
  },
  {
    label: "Ver estoque",
    hint: "Saldo por filial e local",
    template: "qual o estoque do produto {{productCode}}?",
    fields: [{ id: "productCode", label: "Código do produto", fieldType: "productCode" }],
  },
  {
    label: "Capacidades",
    hint: "Ferramentas, dados e limites do agente",
    template: "o que você pode fazer?",
    fields: [],
  },
];

export function buildIcebreakerPlaceholderToken(fieldId: string): string {
  return `{{${fieldId}}}`;
}

function clampText(value: string, maxChars: number): string {
  return value.slice(0, maxChars);
}

export function clampIcebreakerDraft(value: string): string {
  return clampText(value, AGENT_ICEBREAKER_MAX_CHARS);
}

export function clampIcebreakerTitle(value: string): string {
  return clampText(value.trim(), AGENT_ICEBREAKER_TITLE_MAX_CHARS);
}

export function clampIcebreakerHint(value: string): string {
  return clampText(value.trim(), AGENT_ICEBREAKER_HINT_MAX_CHARS);
}

/** Edição ao vivo — não faz trim (evita engolir espaço antes da próxima palavra). */
export function clampIcebreakerTitleDraft(value: string): string {
  return clampText(value, AGENT_ICEBREAKER_TITLE_MAX_CHARS);
}

export function clampIcebreakerHintDraft(value: string): string {
  return clampText(value, AGENT_ICEBREAKER_HINT_MAX_CHARS);
}

function normalizeFieldId(value: string): string {
  const normalized = value
    .trim()
    .replace(/[^\w]/g, "")
    .replace(/^(\d)/, "f$1")
    .slice(0, AGENT_ICEBREAKER_FIELD_ID_MAX_CHARS);

  return normalized || "campo";
}

function inferFieldTypeFromId(fieldId: string): string {
  if (ICEBREAKER_FIELD_TYPE_OPTIONS.some((item) => item.value === fieldId)) {
    return fieldId;
  }

  return "text";
}

function defaultLabelForFieldType(fieldType: string): string {
  return (
    ICEBREAKER_FIELD_TYPE_OPTIONS.find((item) => item.value === fieldType)?.label ??
    "Campo"
  );
}

export function createIcebreakerField(
  index: number,
  fieldType: string = "text",
): IcebreakerFieldConfig {
  const id = `campo${index + 1}`;

  return {
    id,
    label: defaultLabelForFieldType(fieldType),
    fieldType,
    required: true,
  };
}

export function createEmptyIcebreakerEntry(): AgentIcebreakerEntry {
  return {
    label: "",
    hint: "",
    template: "",
    fields: [],
  };
}

function normalizeIcebreakerField(value: unknown): IcebreakerFieldConfig | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  const record = value as Record<string, unknown>;
  const id = normalizeFieldId(String(record.id ?? ""));
  const fieldType = String(record.fieldType ?? record.type ?? inferFieldTypeFromId(id)).trim();
  const label = clampText(String(record.label ?? "").trim(), AGENT_ICEBREAKER_FIELD_LABEL_MAX_CHARS);

  if (!id) {
    return null;
  }

  const placeholder = String(record.placeholder ?? "").trim();

  return {
    id,
    label: label || defaultLabelForFieldType(fieldType),
    fieldType: fieldType || "text",
    required: record.required !== false,
    placeholder: placeholder || undefined,
  };
}

/** Alinha `fields` aos placeholders `{{id}}` presentes no template. */
export function syncIcebreakerEntryFields(entry: AgentIcebreakerEntry): AgentIcebreakerEntry {
  const placeholderIds = listShortcutFieldIds(entry.template);

  if (placeholderIds.length === 0) {
    return { ...entry, fields: [] };
  }

  const existingById = new Map((entry.fields ?? []).map((field) => [field.id, field]));

  const fields = placeholderIds.map((fieldId) => {
    const existing = existingById.get(fieldId);

    if (existing) {
      return existing;
    }

    const fieldType = inferFieldTypeFromId(fieldId);

    return {
      id: fieldId,
      label: defaultLabelForFieldType(fieldType),
      fieldType,
      required: true,
    };
  });

  return { ...entry, fields };
}

function enrichIcebreakerEntry(entry: AgentIcebreakerEntry): AgentIcebreakerEntry {
  return syncIcebreakerEntryFields({
    ...entry,
    label: entry.label?.trim() || undefined,
    hint: entry.hint?.trim() || undefined,
  });
}

function normalizeIcebreakerEntry(value: unknown): AgentIcebreakerEntry | null {
  if (typeof value === "string") {
    const template = clampIcebreakerDraft(value.trim());

    if (!template) {
      return null;
    }

    return enrichIcebreakerEntry({ template });
  }

  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  const record = value as Record<string, unknown>;
  const template = clampIcebreakerDraft(
    String(record.template ?? record.query ?? "").trim(),
  );

  if (!template) {
    return null;
  }

  const label = clampIcebreakerTitle(String(record.label ?? record.title ?? ""));
  const hint = clampIcebreakerHint(String(record.hint ?? record.subtitle ?? ""));
  const rawFields = Array.isArray(record.fields) ? record.fields : [];
  const fields = rawFields
    .map((item) => normalizeIcebreakerField(item))
    .filter((item): item is IcebreakerFieldConfig => item !== null);

  return enrichIcebreakerEntry({
    template,
    label: label || undefined,
    hint: hint || undefined,
    fields,
  });
}

/** Lista efetiva na home — aceita string ou objeto configurável. */
export function normalizeAgentIcebreakerEntries(value: unknown): AgentIcebreakerEntry[] {
  const raw =
    value && typeof value === "object" && !Array.isArray(value)
      ? (value as Record<string, unknown>).icebreakers
      : Array.isArray(value)
        ? value
        : undefined;

  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .map((item) => normalizeIcebreakerEntry(item))
    .filter((item): item is AgentIcebreakerEntry => item !== null);
}

function defaultIcebreakerEntries(): AgentIcebreakerEntry[] {
  return DEFAULT_AGENT_ICEBREAKERS.map((template) => {
    const known = DEFAULT_ICEBREAKER_CATALOG.find((item) => item.template === template);

    if (known) {
      return { ...known };
    }

    return enrichIcebreakerEntry({
      template,
      hint: shortcutFillPromptForTemplate(template),
    });
  });
}

export function normalizeAgentIcebreakers(value: unknown): string[] {
  return normalizeAgentIcebreakerEntries(value).map((entry) => entry.template);
}

/** Valor efetivo na home: configurados ou padrão corporativo. */
export function resolveAgentIcebreakerEntries(metadata: unknown): AgentIcebreakerEntry[] {
  const configured = normalizeAgentIcebreakerEntries(metadata);

  return configured.length > 0 ? configured : defaultIcebreakerEntries();
}

export function resolveAgentIcebreakersForDisplay(metadata: unknown): string[] {
  return resolveAgentIcebreakerEntries(metadata).map((entry) => entry.template);
}

/** Estado inicial do builder. */
export function resolveAgentIcebreakerEntriesForEditor(metadata: unknown): AgentIcebreakerEntry[] {
  const configured = normalizeAgentIcebreakerEntries(metadata);

  if (configured.length > 0) {
    return configured;
  }

  return defaultIcebreakerEntries();
}

/** @deprecated Use resolveAgentIcebreakerEntriesForEditor */
export const resolveAgentIcebreakersForEditor = resolveAgentIcebreakerEntriesForEditor;

function catalogEntryForTemplate(template: string): AgentIcebreakerEntry | undefined {
  return DEFAULT_ICEBREAKER_CATALOG.find((item) => item.template === template);
}

function resolveIcebreakerEntryInput(
  entryOrTemplate: AgentIcebreakerEntry | string,
  overrides?: Pick<AgentIcebreakerEntry, "label" | "hint">,
): AgentIcebreakerEntry {
  if (typeof entryOrTemplate !== "string") {
    return enrichIcebreakerEntry(entryOrTemplate);
  }

  const template = clampIcebreakerDraft(entryOrTemplate.trim());
  const catalog = catalogEntryForTemplate(template);

  return enrichIcebreakerEntry({
    template,
    label: overrides?.label ?? catalog?.label,
    hint: overrides?.hint ?? catalog?.hint,
    fields: catalog?.fields,
  });
}

export function agentIcebreakersUseDefaults(metadata: unknown): boolean {
  return normalizeAgentIcebreakerEntries(metadata).length === 0;
}

export function normalizeIcebreakerEntriesForSave(
  entries: readonly AgentIcebreakerEntry[],
): AgentIcebreakerEntry[] {
  return entries
    .map((entry) => normalizeIcebreakerEntry(entry))
    .filter((entry): entry is AgentIcebreakerEntry => entry !== null)
    .filter((entry) => entry.label?.trim() && entry.template.trim());
}

export function reorderIcebreakerEntries(
  items: readonly AgentIcebreakerEntry[],
  fromIndex: number,
  toIndex: number,
): AgentIcebreakerEntry[] {
  if (
    fromIndex === toIndex ||
    fromIndex < 0 ||
    toIndex < 0 ||
    fromIndex >= items.length ||
    toIndex >= items.length
  ) {
    return [...items];
  }

  const next = [...items];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);

  return next;
}

export function resolveIcebreakerShortcutFields(
  entry: AgentIcebreakerEntry,
): ShortcutFieldDefinition[] {
  return resolveShortcutFields(entry.template, entry.fields);
}

export function resolveIcebreakerPromptOptions(entry: AgentIcebreakerEntry): {
  title?: string;
  description?: string;
  fields?: ShortcutFieldDefinition[];
} {
  return {
    title: entry.label?.trim() || undefined,
    description: entry.hint?.trim() || undefined,
    fields: resolveIcebreakerShortcutFields(entry),
  };
}

export function icebreakerRequiresShortcutModal(entry: AgentIcebreakerEntry): boolean {
  if (!hasShortcutPlaceholders(entry.template)) {
    return false;
  }

  return resolveIcebreakerShortcutFields(entry).length > 0;
}

export { formatShortcutTemplateForDisplay, hasShortcutPlaceholders };

/** Texto exibido no card (pode truncar; o clique envia o template com `{{campo}}`). */
export function formatIcebreakerForDisplay(
  text: string,
  maxChars: number = AGENT_ICEBREAKER_MAX_CHARS,
): string {
  const trimmed = formatShortcutTemplateForDisplay(text);

  if (trimmed.length <= maxChars) {
    return trimmed;
  }

  return `${trimmed.slice(0, Math.max(0, maxChars - 1)).trimEnd()}…`;
}

export type IcebreakerCardPresentation = {
  title: string;
  subtitle?: string;
};

/** Rótulo curto + subtítulo para cards da home do agente. */
export function resolveIcebreakerCardPresentation(
  entryOrTemplate: AgentIcebreakerEntry | string,
  overrides?: Pick<AgentIcebreakerEntry, "label" | "hint">,
): IcebreakerCardPresentation {
  const entry = resolveIcebreakerEntryInput(entryOrTemplate, overrides);
  const title =
    entry.label?.trim() ||
    entry.template.replace(/\{\{[^}]+\}\}/g, "").replace(/\s+/g, " ").trim() ||
    "Sugestão";

  const subtitle =
    entry.hint?.trim() ||
    (entry.fields && entry.fields.length > 0
      ? entry.fields.map((field) => field.label).join(" · ")
      : shortcutFillPromptForTemplate(entry.template));

  return {
    title,
    subtitle: subtitle || undefined,
  };
}

/** Variante visual do card (ícone e cor de destaque). */
export function resolveIcebreakerVisualKind(
  entryOrTemplate: AgentIcebreakerEntry | string,
): IcebreakerVisualKind {
  const entry = resolveIcebreakerEntryInput(entryOrTemplate);
  const normalized = entry.template.trim();
  const fieldTypes = (entry.fields ?? []).map((field) => field.fieldType);

  if (fieldTypes.includes("searchQuery") || normalized.includes("{{searchQuery}}")) {
    return "web";
  }

  if (fieldTypes.includes("textContent") || normalized.includes("{{textContent}}")) {
    return "text";
  }

  if (/o que você pode fazer/i.test(normalized)) {
    return "capabilities";
  }

  if (
    (fieldTypes.includes("productCode") || normalized.includes("{{productCode}}")) &&
    /estoque/i.test(normalized)
  ) {
    return "stock";
  }

  if (fieldTypes.includes("productCode") || normalized.includes("{{productCode}}")) {
    return "product";
  }

  return "generic";
}

/** Classe de densidade do grid conforme a quantidade de sugestões. */
export function getIcebreakerGridDensityClass(count: number): string {
  if (count <= 3) {
    return "mdc-chat-agent-landing__prompts-grid--few";
  }

  if (count === 4) {
    return "mdc-chat-agent-landing__prompts-grid--quad";
  }

  return "mdc-chat-agent-landing__prompts-grid--many";
}

/** @deprecated Use reorderIcebreakerEntries */
export function reorderIcebreakers(
  items: readonly string[],
  fromIndex: number,
  toIndex: number,
): string[] {
  if (
    fromIndex === toIndex ||
    fromIndex < 0 ||
    toIndex < 0 ||
    fromIndex >= items.length ||
    toIndex >= items.length
  ) {
    return [...items];
  }

  const next = [...items];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);

  return next;
}
