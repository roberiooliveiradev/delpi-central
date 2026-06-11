import type { ChatToolCall } from "../../data/api/chatTypes";

import type { StackSectionId } from "./presentationStackSections";
import {
  isMultiRouteProductPresentation,
  resolveMultiRouteStackPlan,
} from "./presentationMultiRoute";

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

export type TailVisualPolicy = "allowlist" | "legacy";

export type PresentationRenderHints = {
  textRenderMode?: "compact" | "full";
  tailVisualPolicy?: TailVisualPolicy;
  suppressedKinds?: string[];
};

export type StackPresentationPlan = {
  profileFirst: boolean;
  highlightsAfterProfile: boolean;
  attentionLast: boolean;
  tableRoleOrder: StackTableRole[];
  tailVisualOrder: string[];
  narrativeOrder: StackNarrativeSlot[];
  /** Playbook 13 — narrativa no chat + evidências em componentes. */
  presentationMode?: string;
  /** allowlist: só renderiza visuais listados em tailVisualOrder (sem fallback órfão). */
  tailVisualPolicy?: TailVisualPolicy;
  /** Telemetria/contrato P6 — texto já preparado na API quando `compact`. */
  renderHints?: PresentationRenderHints;
  /** Inteligência da API: mockup humanizado no analyser e rotas compostas de produto. */
  presentationProfile?: string;
  humanizedSections?: boolean;
  sectionVisibility?: Partial<Record<StackSectionId, boolean>>;
  /** Texto explicativo por seção (API) — renderizado como markdown normal, sem repetir tabela/bullets. */
  sectionFraming?: Partial<Record<StackSectionId, string>>;
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

function normalizeSectionFraming(
  value: unknown,
): Partial<Record<StackSectionId, string>> | undefined {
  if (!value || typeof value !== "object") {
    return undefined;
  }

  const allowed = new Set<StackSectionId>([
    "scope",
    "profile",
    "highlights",
    "guide",
    "inspection",
    "structure",
    "attention",
  ]);
  const intros: Partial<Record<StackSectionId, string>> = {};

  for (const [key, text] of Object.entries(value as Record<string, unknown>)) {
    if (!allowed.has(key as StackSectionId)) {
      continue;
    }

    const trimmed = String(text || "").trim();

    if (trimmed) {
      intros[key as StackSectionId] = trimmed;
    }
  }

  return Object.keys(intros).length ? intros : undefined;
}

function normalizeSectionVisibility(
  value: unknown,
): Partial<Record<StackSectionId, boolean>> | undefined {
  if (!value || typeof value !== "object") {
    return undefined;
  }

  const allowed = new Set<StackSectionId>([
    "scope",
    "profile",
    "highlights",
    "guide",
    "inspection",
    "structure",
    "attention",
  ]);
  const visibility: Partial<Record<StackSectionId, boolean>> = {};

  for (const [key, flag] of Object.entries(value as Record<string, unknown>)) {
    if (allowed.has(key as StackSectionId)) {
      visibility[key as StackSectionId] = flag === true;
    }
  }

  return Object.keys(visibility).length ? visibility : undefined;
}

const LEGACY_PRESENTATION_PROFILES = new Set([
  "product_analyser",
  "product_factory_status",
  "product_production_status",
  "product_shipping_status",
  "product_structure_exclusivity",
  "generic_stack",
]);

function resolvePresentationProfile(
  profile: string,
  humanizedSections: boolean,
): string | undefined {
  const trimmed = profile.trim();

  if (!trimmed) {
    return undefined;
  }

  if (humanizedSections || LEGACY_PRESENTATION_PROFILES.has(trimmed)) {
    return trimmed;
  }

  return undefined;
}

function normalizeTailVisualPolicy(value: unknown): TailVisualPolicy | undefined {
  const token = String(value || "").trim().toLowerCase();

  if (token === "allowlist" || token === "legacy") {
    return token;
  }

  return undefined;
}

function normalizeRenderHints(value: unknown): PresentationRenderHints | undefined {
  if (!value || typeof value !== "object") {
    return undefined;
  }

  const raw = value as Record<string, unknown>;
  const textRenderMode = String(raw.textRenderMode || "").trim().toLowerCase();
  const tailVisualPolicy = normalizeTailVisualPolicy(raw.tailVisualPolicy);
  const hints: PresentationRenderHints = {};

  if (textRenderMode === "compact" || textRenderMode === "full") {
    hints.textRenderMode = textRenderMode;
  }

  if (tailVisualPolicy) {
    hints.tailVisualPolicy = tailVisualPolicy;
  }

  if (Array.isArray(raw.suppressedKinds)) {
    hints.suppressedKinds = raw.suppressedKinds.map((item) => String(item));
  }

  return Object.keys(hints).length ? hints : undefined;
}

function parsePlan(raw: Record<string, unknown>): StackPresentationPlan {
  const profile = String(raw.presentationProfile || "").trim();
  const humanizedSections = raw.humanizedSections === true;
  const presentationMode = String(raw.presentationMode || "").trim() || undefined;
  const tailVisualPolicy = normalizeTailVisualPolicy(raw.tailVisualPolicy);

  return {
    profileFirst: raw.profileFirst !== false,
    highlightsAfterProfile: raw.highlightsAfterProfile !== false,
    attentionLast: raw.attentionLast !== false,
    tableRoleOrder: normalizeTableRoles(raw.tableRoleOrder),
    tailVisualOrder: Array.isArray(raw.tailVisualOrder)
      ? raw.tailVisualOrder.map((item) => String(item))
      : DEFAULT_PLAN.tailVisualOrder,
    narrativeOrder: normalizeNarrativeOrder(raw.narrativeOrder),
    presentationMode,
    tailVisualPolicy,
    renderHints: normalizeRenderHints(raw.renderHints),
    presentationProfile: resolvePresentationProfile(profile, humanizedSections),
    humanizedSections,
    sectionVisibility: normalizeSectionVisibility(raw.sectionVisibility),
    sectionFraming: normalizeSectionFraming(
      raw.sectionFraming ?? raw.sectionIntros,
    ),
  };
}

export function usesStrictTailVisualAllowlist(plan: StackPresentationPlan): boolean {
  return plan.tailVisualPolicy === "allowlist";
}

export function planUsesHumanizedSections(plan: StackPresentationPlan): boolean {
  return plan.humanizedSections === true;
}

export function getStackPresentationPlanFromToolCalls(
  toolCalls?: ChatToolCall[],
): StackPresentationPlan {
  if (!Array.isArray(toolCalls)) {
    return DEFAULT_PLAN;
  }

  if (isMultiRouteProductPresentation(toolCalls)) {
    return resolveMultiRouteStackPlan(toolCalls);
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
  }

  return DEFAULT_PLAN;
}

const STACK_TABLE_ROLES = new Set<StackTableRole>([
  "profile",
  "guide",
  "inspection",
  "stock",
  "pricing",
  "structure",
  "list",
  "other",
]);

/**
 * @deprecated Prefer `presentation.role` from API metadata. Fallback legacy por título.
 */
export function inferTableRoleFromTitle(title: string): StackTableRole {
  const normalized = title.trim().toLowerCase();

  if (
    normalized.includes("panorama fabril") ||
    normalized.includes("resumo produtivo") ||
    normalized.includes("resumo de expedição") ||
    normalized.includes("resumo de expedicao") ||
    normalized.includes("resumo da estrutura") ||
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
    normalized.includes("armazem") ||
    normalized.includes("matéria") ||
    normalized.includes("materia")
  ) {
    return "stock";
  }

  if (
    normalized.includes("produção") ||
    normalized.includes("producao") ||
    normalized.includes("apontamento") ||
    normalized.includes("ordens") ||
    normalized.includes("movimentos de expedição") ||
    normalized.includes("movimentos de expedicao")
  ) {
    return "list";
  }

  if (normalized.includes("expedição") || normalized.includes("expedicao")) {
    return "list";
  }

  if (
    normalized.includes("exclusividade") ||
    normalized.includes("componentes com exclusividade")
  ) {
    return "structure";
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

export function resolveTableRole(
  title: string,
  presentation?: { role?: string | null },
): StackTableRole {
  const role = String(presentation?.role || "").trim() as StackTableRole;

  if (role && STACK_TABLE_ROLES.has(role)) {
    return role;
  }

  return inferTableRoleFromTitle(title);
}
