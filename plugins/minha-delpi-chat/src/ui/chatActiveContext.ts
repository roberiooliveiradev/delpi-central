import type { ChatContextChip } from "./components/ChatContextBar";

const CHIP_KIND_ORDER: Record<string, number> = {
  product: 0,
  branch: 1,
  warehouse: 2,
  topic: 3,
  task: 4,
  period: 5,
  attachment: 6,
  canvas: 7,
  format: 8,
  tone: 9,
  preference: 10,
  email: 11,
  textCorrection: 12,
};

export function contextChipKey(chip: Pick<ChatContextChip, "kind" | "value">): string {
  return `${chip.kind}:${chip.value}`;
}

function isContextChip(value: unknown): value is ChatContextChip {
  if (!value || typeof value !== "object") {
    return false;
  }

  const chip = value as ChatContextChip;

  return (
    typeof chip.kind === "string" &&
    chip.kind.trim().length > 0 &&
    typeof chip.value === "string" &&
    chip.value.trim().length > 0 &&
    typeof chip.label === "string" &&
    chip.label.trim().length > 0
  );
}

export function normalizeContextChips(raw: unknown): ChatContextChip[] {
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw.filter(isContextChip).map((chip) => ({
    kind: chip.kind.trim(),
    value: chip.value.trim(),
    label: chip.label.trim(),
  }));
}

/** Une chips de vários turnos (produto + filial + preferências, etc.) sem duplicar kind+value. */
export function mergeContextChips(batches: ChatContextChip[][]): ChatContextChip[] {
  const byKey = new Map<string, ChatContextChip>();

  for (const batch of batches) {
    for (const chip of batch) {
      byKey.set(contextChipKey(chip), chip);
    }
  }

  return [...byKey.values()].sort((left, right) => {
    const leftOrder = CHIP_KIND_ORDER[left.kind] ?? 50;
    const rightOrder = CHIP_KIND_ORDER[right.kind] ?? 50;

    if (leftOrder !== rightOrder) {
      return leftOrder - rightOrder;
    }

    return left.label.localeCompare(right.label, "pt-BR");
  });
}

type MessageWithContext = {
  role?: string | null;
  metadata?: Record<string, unknown> | null;
};

/**
 * Agrega contexto das últimas respostas do assistente (mais recente prevalece no mesmo kind+value).
 */
export function collectActiveContextChips(
  messages: MessageWithContext[],
  maxAssistantTurns = 12,
): ChatContextChip[] {
  const batches: ChatContextChip[][] = [];

  for (let index = messages.length - 1; index >= 0 && batches.length < maxAssistantTurns; index -= 1) {
    const message = messages[index];

    if (message.role !== "assistant") {
      continue;
    }

    const chips = normalizeContextChips(message.metadata?.contextChips);

    if (chips.length > 0) {
      batches.push(chips);
    }
  }

  return mergeContextChips(batches.reverse());
}

export function contextChipKindClass(kind: string): string {
  const safe = kind.replace(/[^a-z0-9_-]/gi, "");

  return safe ? `mdc-chat-context-bar__chip--${safe}` : "mdc-chat-context-bar__chip--generic";
}

const PINNABLE_CONTEXT_KINDS = new Set(["branch", "warehouse", "product"]);
const USER_CONTEXT_ITEM_KINDS = new Set(["note", "table", "file", "knowledge"]);

export function isPinnableContextKind(kind: string): boolean {
  return PINNABLE_CONTEXT_KINDS.has(String(kind || "").trim().toLowerCase());
}

export function isUserContextItemKind(kind: string): boolean {
  return USER_CONTEXT_ITEM_KINDS.has(String(kind || "").trim().toLowerCase());
}

export function buildActiveContextSummary(chips: ChatContextChip[]): string | null {
  if (!chips.length) {
    return null;
  }

  return chips.map((chip) => chip.label).join(" · ");
}

export type MemoryUsageView = {
  layers?: string[];
  topic?: string | null;
  task?: string | null;
  entities?: Record<string, string>;
  preferences?: string[];
  resolvedReferences?: string[];
  semanticHits?: Array<{ title?: string; snippet?: string }>;
  episodicCount?: number;
  episodicRecall?: string | null;
  writeGated?: boolean;
  userContextItems?: string[];
};

export function extractMemoryUsageFromMessages(
  messages: MessageWithContext[],
): MemoryUsageView | null {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];

    if (message.role !== "assistant") {
      continue;
    }

    const raw = message.metadata?.memoryUx;

    if (!raw || typeof raw !== "object") {
      continue;
    }

    const usage = (raw as { usage?: MemoryUsageView }).usage;

    if (usage && typeof usage === "object") {
      return usage;
    }
  }

  return null;
}

export function extractActivePreferenceHint(chips: ChatContextChip[]): string | null {
  const preference = chips.find(
    (chip) =>
      chip.kind === "preference" ||
      chip.kind === "tone" ||
      chip.kind === "format" ||
      chip.kind === "textCorrection" ||
      chip.kind === "email",
  );

  return preference ? `Preferência ativa: ${preference.label}` : null;
}

