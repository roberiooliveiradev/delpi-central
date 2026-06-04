import type { ChatToolCall } from "../../data/api/chatTypes";

export type StackTableRole =
  | "profile"
  | "guide"
  | "inspection"
  | "stock"
  | "pricing"
  | "structure"
  | "list"
  | "other";

export type StackNarrativeSlot =
  | "lead"
  | "profileTables"
  | "highlights"
  | "operationalTables"
  | "tailVisuals"
  | "attention";

export type StackPresentationPlan = {
  profileFirst: boolean;
  highlightsAfterProfile: boolean;
  attentionLast: boolean;
  tableRoleOrder: StackTableRole[];
  tailVisualOrder: string[];
  narrativeOrder: StackNarrativeSlot[];
};

const DEFAULT_TABLE_ROLE_ORDER: StackTableRole[] = [
  "profile",
  "guide",
  "inspection",
  "stock",
  "pricing",
  "structure",
  "list",
  "other",
];

const DEFAULT_NARRATIVE_ORDER: StackNarrativeSlot[] = [
  "lead",
  "profileTables",
  "highlights",
  "operationalTables",
  "tailVisuals",
  "attention",
];

const DEFAULT_PLAN: StackPresentationPlan = {
  profileFirst: true,
  highlightsAfterProfile: true,
  attentionLast: true,
  tableRoleOrder: DEFAULT_TABLE_ROLE_ORDER,
  tailVisualOrder: ["tree", "chart", "kpi", "dashboard"],
  narrativeOrder: DEFAULT_NARRATIVE_ORDER,
};

function normalizeTableRoles(value: unknown): StackTableRole[] {
  if (!Array.isArray(value)) {
    return DEFAULT_TABLE_ROLE_ORDER;
  }

  const allowed = new Set(DEFAULT_TABLE_ROLE_ORDER);
  const roles = value
    .map((item) => String(item || "").trim() as StackTableRole)
    .filter((role) => allowed.has(role));

  return roles.length ? roles : DEFAULT_TABLE_ROLE_ORDER;
}

function normalizeNarrativeOrder(value: unknown): StackNarrativeSlot[] {
  if (!Array.isArray(value)) {
    return DEFAULT_NARRATIVE_ORDER;
  }

  const allowed = new Set(DEFAULT_NARRATIVE_ORDER);
  const slots = value
    .map((item) => String(item || "").trim() as StackNarrativeSlot)
    .filter((slot) => allowed.has(slot));

  return slots.length ? slots : DEFAULT_NARRATIVE_ORDER;
}

function parsePlan(raw: Record<string, unknown>): StackPresentationPlan {
  return {
    profileFirst: raw.profileFirst !== false,
    highlightsAfterProfile: raw.highlightsAfterProfile !== false,
    attentionLast: raw.attentionLast !== false,
    tableRoleOrder: normalizeTableRoles(raw.tableRoleOrder),
    tailVisualOrder: Array.isArray(raw.tailVisualOrder)
      ? raw.tailVisualOrder.map((item) => String(item))
      : DEFAULT_PLAN.tailVisualOrder,
    narrativeOrder: normalizeNarrativeOrder(raw.narrativeOrder),
  };
}

export function getStackPresentationPlanFromToolCalls(
  toolCalls?: ChatToolCall[],
): StackPresentationPlan {
  if (!Array.isArray(toolCalls)) {
    return DEFAULT_PLAN;
  }

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const raw =
      metadata.stackPresentationPlan ??
      (metadata.presentationDecision as Record<string, unknown> | undefined)
        ?.stackPresentationPlan;

    if (raw && typeof raw === "object") {
      return parsePlan(raw as Record<string, unknown>);
    }

    const path = String(metadata.path ?? "").toLowerCase();

    if (path.includes("/analyser")) {
      return {
        ...DEFAULT_PLAN,
        tableRoleOrder: ["profile", "guide", "inspection", "other"],
        attentionLast: true,
        highlightsAfterProfile: true,
      };
    }

    if (path.includes("/stock")) {
      return {
        ...DEFAULT_PLAN,
        tableRoleOrder: ["profile", "stock", "other"],
      };
    }
  }

  return DEFAULT_PLAN;
}

export function inferTableRoleFromTitle(title: string): StackTableRole {
  const normalized = title.trim().toLowerCase();

  if (
    normalized.startsWith("produto ") ||
    normalized.includes("cadastro") ||
    normalized.includes("ficha")
  ) {
    return "profile";
  }

  if (normalized.includes("roteiro") || normalized.includes("/guide")) {
    return "guide";
  }

  if (normalized.includes("inspeção") || normalized.includes("inspecao")) {
    return "inspection";
  }

  if (
    normalized.includes("estoque") ||
    normalized.includes("saldo") ||
    normalized.includes("armazém") ||
    normalized.includes("armazem")
  ) {
    return "stock";
  }

  if (
    normalized.includes("preço") ||
    normalized.includes("preco") ||
    normalized.includes("pricing")
  ) {
    return "pricing";
  }

  if (
    normalized.includes("estrutura") ||
    normalized.includes("composição") ||
    normalized.includes("composicao") ||
    normalized.includes("componentes")
  ) {
    return "structure";
  }

  if (
    normalized.includes("lista") ||
    normalized.includes("resultado") ||
    normalized.includes("consulta")
  ) {
    return "list";
  }

  return "other";
}
