import type { LucideIcon } from "lucide-react";

import {
  defaultPageForSubTab,
  hasNestedPages,
  nestedPageFromSlug,
  nestedPageSlug,
} from "./adminNavPages";
import {
  BarChart3,
  BookOpen,
  Bot,
  LayoutDashboard,
  Shield,
  Wrench,
} from "lucide-react";

const CHAT_BASE_PATH = "/apps/minha-delpi-chat";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isAgentIdSegment(value: string): boolean {
  return UUID_RE.test(decodeURIComponent(value).trim());
}

/**
 * @deprecated Abas planas pré-shell v3. Preferir `AdminNavState` / rotas `/admin/<section>/<sub>`.
 * Mantido só para mapear bookmarks antigos em testes.
 */
export type AdminLegacyTab =
  | "knowledge"
  | "metrics"
  | "guidelines"
  | "skills"
  | "simulate"
  | "evaluations"
  | "agents"
  | "security"
  | "tools"
  | "audit";

export type AdminSection =
  | "overview"
  | "knowledge"
  | "agents"
  | "quality"
  | "platform"
  | "governance";

export type AdminSubTab =
  | "documents"
  | "guidelines"
  | "behaviors"
  | "learning"
  | "specialization"
  | "simulation"
  | "metrics"
  | "evaluations"
  | "tools"
  | "intelligence"
  | "response"
  | "vision"
  | "security"
  | "audit";

export type AdminNavState = {
  section: AdminSection;
  subTab?: AdminSubTab;
  /** Página interna da sub-aba (ex.: candidatos em aprendizagem). */
  page?: string;
};

export type AdminSectionItem = {
  key: AdminSection;
  label: string;
  description: string;
  icon: LucideIcon;
  subTabs: Array<{ key: AdminSubTab; label: string }>;
};

/** Slugs canônicos EN (english-code-identifiers). */
const SECTION_SLUG: Record<AdminSection, string> = {
  overview: "overview",
  knowledge: "knowledge",
  agents: "agents",
  quality: "quality",
  platform: "platform",
  governance: "governance",
};

/** PT legado + EN → seção (parse dual). */
const SLUG_TO_SECTION: Record<string, AdminSection> = {
  overview: "overview",
  painel: "overview",
  knowledge: "knowledge",
  conhecimento: "knowledge",
  agents: "agents",
  agentes: "agents",
  quality: "quality",
  qualidade: "quality",
  platform: "platform",
  plataforma: "platform",
  governance: "governance",
  governanca: "governance",
};

/** Slugs canônicos EN. */
const SUB_SLUG: Record<AdminSubTab, string> = {
  documents: "documents",
  guidelines: "guidelines",
  behaviors: "behaviors",
  learning: "learning",
  specialization: "specialization",
  simulation: "simulation",
  metrics: "metrics",
  evaluations: "evaluations",
  tools: "tools",
  intelligence: "intelligence",
  response: "response-modes",
  vision: "vision",
  security: "security",
  audit: "audit",
};

/** PT legado + EN → sub-aba. */
const SLUG_TO_SUB: Record<string, AdminSubTab> = {
  documents: "documents",
  documentos: "documents",
  guidelines: "guidelines",
  diretrizes: "guidelines",
  behaviors: "behaviors",
  comportamentos: "behaviors",
  learning: "learning",
  aprendizagem: "learning",
  specialization: "specialization",
  especializacao: "specialization",
  simulation: "simulation",
  simulacao: "simulation",
  metrics: "metrics",
  metricas: "metrics",
  evaluations: "evaluations",
  avaliacoes: "evaluations",
  tools: "tools",
  ferramentas: "tools",
  intelligence: "intelligence",
  inteligencia: "intelligence",
  "response-modes": "response",
  "modos-resposta": "response",
  vision: "vision",
  visao: "vision",
  security: "security",
  seguranca: "security",
  audit: "audit",
  auditoria: "audit",
};

const AGENTS_SECTION_SLUGS = new Set(["agents", "agentes"]);
const SPECIALIZATION_SUB_SLUGS = new Set(["specialization", "especializacao"]);

export function isAdminAgentsSectionSlug(slug: string | undefined): boolean {
  return Boolean(slug && AGENTS_SECTION_SLUGS.has(slug));
}

export function isAdminSpecializationSubSlug(slug: string | undefined): boolean {
  return Boolean(slug && SPECIALIZATION_SUB_SLUGS.has(slug));
}

export const ADMIN_SECTIONS: AdminSectionItem[] = [
  {
    key: "overview",
    label: "Painel",
    description: "Visão geral e permissões do administrador.",
    icon: LayoutDashboard,
    subTabs: [],
  },
  {
    key: "knowledge",
    label: "Conhecimento",
    description: "Documentos, diretrizes e comportamentos globais.",
    icon: BookOpen,
    subTabs: [
      { key: "documents", label: "Documentos" },
      { key: "guidelines", label: "Diretrizes" },
      { key: "behaviors", label: "Comportamentos" },
      { key: "learning", label: "Aprendizagem" },
    ],
  },
  {
    key: "agents",
    label: "Agentes",
    description: "Especialização e simulação por agente.",
    icon: Bot,
    subTabs: [
      { key: "specialization", label: "Especialização" },
      { key: "simulation", label: "Simulação" },
    ],
  },
  {
    key: "quality",
    label: "Qualidade",
    description: "Métricas operacionais e avaliações de resposta.",
    icon: BarChart3,
    subTabs: [
      { key: "metrics", label: "Métricas" },
      { key: "evaluations", label: "Avaliações" },
    ],
  },
  {
    key: "platform",
    label: "Plataforma",
    description: "Ferramentas, LLM e políticas de inteligência.",
    icon: Wrench,
    subTabs: [
      { key: "tools", label: "Ferramentas" },
      { key: "intelligence", label: "Inteligência" },
      { key: "response", label: "Modos de resposta" },
      { key: "vision", label: "Visão e anexos" },
    ],
  },
  {
    key: "governance",
    label: "Governança",
    description: "Segurança operacional e trilha de auditoria.",
    icon: Shield,
    subTabs: [
      { key: "security", label: "Segurança" },
      { key: "audit", label: "Auditoria" },
    ],
  },
];

const DEFAULT_SUB_TAB: Record<Exclude<AdminSection, "overview">, AdminSubTab> = {
  knowledge: "documents",
  agents: "specialization",
  quality: "metrics",
  platform: "tools",
  governance: "security",
};

export function defaultSubTabForSection(section: AdminSection): AdminSubTab | undefined {
  if (section === "overview") {
    return undefined;
  }

  return DEFAULT_SUB_TAB[section];
}

export function normalizeAdminNav(
  partial: Partial<AdminNavState> | null | undefined,
): AdminNavState {
  const section = partial?.section ?? "overview";

  if (section === "overview") {
    return { section: "overview" };
  }

  const subTab = partial?.subTab ?? defaultSubTabForSection(section);
  const page =
    partial?.page ??
    (subTab && hasNestedPages(subTab) ? defaultPageForSubTab(subTab) : undefined);

  if (!page) {
    return { section, subTab };
  }

  return { section, subTab, page };
}

/** @deprecated Preferir `AdminNavState` direto. */
export function legacyTabToNav(tab: AdminLegacyTab): AdminNavState {
  switch (tab) {
    case "knowledge":
      return { section: "knowledge", subTab: "documents" };
    case "guidelines":
      return { section: "knowledge", subTab: "guidelines" };
    case "skills":
      return { section: "knowledge", subTab: "behaviors" };
    case "agents":
      return { section: "agents", subTab: "specialization" };
    case "simulate":
      return { section: "agents", subTab: "simulation" };
    case "metrics":
      return { section: "quality", subTab: "metrics" };
    case "evaluations":
      return { section: "quality", subTab: "evaluations" };
    case "tools":
      return { section: "platform", subTab: "tools" };
    case "security":
      return { section: "governance", subTab: "security" };
    case "audit":
      return { section: "governance", subTab: "audit" };
    default:
      return { section: "overview" };
  }
}

export function getAdminSectionItem(section: AdminSection): AdminSectionItem {
  return ADMIN_SECTIONS.find((item) => item.key === section) ?? ADMIN_SECTIONS[0];
}

export function parseAdminPathSegments(segments: string[]): AdminNavState | null {
  if (segments.length === 0) {
    return { section: "overview" };
  }

  const [first, second] = segments;

  if (isAdminAgentsSectionSlug(first) && second && isAgentIdSegment(second)) {
    return null;
  }

  const section = SLUG_TO_SECTION[first];

  if (!section) {
    return null;
  }

  if (section === "overview") {
    return { section: "overview" };
  }

  if (!second) {
    return { section: "overview" };
  }

  const subTab = SLUG_TO_SUB[second];

  if (!subTab) {
    return { section: "overview" };
  }

  const third = segments[2];
  const page =
    third && hasNestedPages(subTab) ? nestedPageFromSlug(subTab, third) : undefined;

  return normalizeAdminNav({ section, subTab, page });
}

export function buildAdminHref(nav: AdminNavState): string {
  const normalized = normalizeAdminNav(nav);

  if (normalized.section === "overview") {
    return `${CHAT_BASE_PATH}/admin`;
  }

  const sectionSlug = SECTION_SLUG[normalized.section];
  const subTab = normalized.subTab ?? defaultSubTabForSection(normalized.section);
  const subSlug = subTab ? SUB_SLUG[subTab] : "";
  const pageSlug =
    subTab && normalized.page ? nestedPageSlug(subTab, normalized.page) : undefined;

  if (pageSlug) {
    return `${CHAT_BASE_PATH}/admin/${sectionSlug}/${subSlug}/${pageSlug}`;
  }

  return `${CHAT_BASE_PATH}/admin/${sectionSlug}/${subSlug}`;
}

export function buildAdminAgentHref(agentId: string): string {
  return `${CHAT_BASE_PATH}/admin/${SECTION_SLUG.agents}/${SUB_SLUG.specialization}/${encodeURIComponent(agentId)}`;
}
