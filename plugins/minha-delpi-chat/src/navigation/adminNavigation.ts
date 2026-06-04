import type { LucideIcon } from "lucide-react";
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

/** @deprecated Abas planas legadas — use AdminSection + AdminSubTab */
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
  | "security"
  | "audit";

export type AdminNavState = {
  section: AdminSection;
  subTab?: AdminSubTab;
};

export type AdminSectionItem = {
  key: AdminSection;
  label: string;
  description: string;
  icon: LucideIcon;
  subTabs: Array<{ key: AdminSubTab; label: string }>;
};

const SECTION_SLUG: Record<AdminSection, string> = {
  overview: "painel",
  knowledge: "conhecimento",
  agents: "agentes",
  quality: "qualidade",
  platform: "plataforma",
  governance: "governanca",
};

const SLUG_TO_SECTION: Record<string, AdminSection> = Object.fromEntries(
  Object.entries(SECTION_SLUG).map(([section, slug]) => [slug, section as AdminSection]),
) as Record<string, AdminSection>;

const SUB_SLUG: Record<AdminSubTab, string> = {
  documents: "documentos",
  guidelines: "diretrizes",
  behaviors: "comportamentos",
  learning: "aprendizagem",
  specialization: "especializacao",
  simulation: "simulacao",
  metrics: "metricas",
  evaluations: "avaliacoes",
  tools: "ferramentas",
  intelligence: "inteligencia",
  security: "seguranca",
  audit: "auditoria",
};

const SLUG_TO_SUB: Record<string, AdminSubTab> = Object.fromEntries(
  Object.entries(SUB_SLUG).map(([sub, slug]) => [slug, sub as AdminSubTab]),
) as Record<string, AdminSubTab>;

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

  return { section, subTab };
}

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

export function warnLegacyAdminTab(tab: AdminLegacyTab) {
  if (typeof import.meta !== "undefined" && import.meta.env?.DEV) {
    console.warn(
      `[minha-delpi-chat] AdminTab legado "${tab}" — use rotas /admin/<seção>/<sub-aba>.`,
      legacyTabToNav(tab),
    );
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

  if (first === "agentes" && second && isAgentIdSegment(second)) {
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

  return normalizeAdminNav({ section, subTab });
}

export function buildAdminHref(nav: AdminNavState): string {
  const normalized = normalizeAdminNav(nav);

  if (normalized.section === "overview") {
    return `${CHAT_BASE_PATH}/admin`;
  }

  const sectionSlug = SECTION_SLUG[normalized.section];
  const subTab = normalized.subTab ?? defaultSubTabForSection(normalized.section);
  const subSlug = subTab ? SUB_SLUG[subTab] : "";

  return `${CHAT_BASE_PATH}/admin/${sectionSlug}/${subSlug}`;
}

export function buildAdminAgentHref(agentId: string): string {
  return `${CHAT_BASE_PATH}/admin/agentes/especializacao/${encodeURIComponent(agentId)}`;
}
