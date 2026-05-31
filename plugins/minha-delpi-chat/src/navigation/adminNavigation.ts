import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  BookOpen,
  Bot,
  LayoutDashboard,
  Shield,
  Wrench,
} from "lucide-react";

import { CHAT_BASE_PATH } from "./chatRoutes";

/** @deprecated Use AdminSection + AdminSubTab — mantido para redirects legados */
export type LegacyAdminTab =
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
  subTab: AdminSubTab | null;
  agentId?: string | null;
};

export type AdminSectionConfig = {
  key: AdminSection;
  label: string;
  description: string;
  icon: LucideIcon;
  subTabs: { key: AdminSubTab; label: string }[];
};

export const ADMIN_SECTIONS: AdminSectionConfig[] = [
  {
    key: "overview",
    label: "Painel",
    description: "Visão geral da saúde do chat, permissões e atalhos.",
    icon: LayoutDashboard,
    subTabs: [],
  },
  {
    key: "knowledge",
    label: "Conhecimento",
    description: "Documentos, diretrizes e comportamentos do assistente.",
    icon: BookOpen,
    subTabs: [
      { key: "documents", label: "Documentos" },
      { key: "guidelines", label: "Diretrizes" },
      { key: "behaviors", label: "Comportamentos" },
    ],
  },
  {
    key: "agents",
    label: "Agentes",
    description: "Especialização por agente e simulação de respostas.",
    icon: Bot,
    subTabs: [
      { key: "specialization", label: "Especialização" },
      { key: "simulation", label: "Simulação" },
    ],
  },
  {
    key: "quality",
    label: "Qualidade",
    description: "Métricas operacionais e avaliações de respostas.",
    icon: BarChart3,
    subTabs: [
      { key: "metrics", label: "Métricas" },
      { key: "evaluations", label: "Avaliações" },
    ],
  },
  {
    key: "platform",
    label: "Plataforma",
    description: "Ferramentas, providers e configuração de inteligência.",
    icon: Wrench,
    subTabs: [
      { key: "tools", label: "Ferramentas" },
      { key: "intelligence", label: "Inteligência" },
    ],
  },
  {
    key: "governance",
    label: "Governança",
    description: "Segurança, anti-injection e trilha de auditoria.",
    icon: Shield,
    subTabs: [
      { key: "security", label: "Segurança" },
      { key: "audit", label: "Auditoria" },
    ],
  },
];

const SECTION_SLUG: Record<AdminSection, string> = {
  overview: "",
  knowledge: "conhecimento",
  agents: "agentes",
  quality: "qualidade",
  platform: "plataforma",
  governance: "governanca",
};

const SUB_TAB_SLUG: Record<AdminSubTab, string> = {
  documents: "documentos",
  guidelines: "diretrizes",
  behaviors: "comportamentos",
  specialization: "especializacao",
  simulation: "simulacao",
  metrics: "metricas",
  evaluations: "avaliacoes",
  tools: "ferramentas",
  intelligence: "inteligencia",
  security: "seguranca",
  audit: "auditoria",
};

const SECTION_BY_SLUG = Object.fromEntries(
  Object.entries(SECTION_SLUG).map(([section, slug]) => [slug, section as AdminSection]),
) as Record<string, AdminSection>;

const SUB_TAB_BY_SLUG = Object.fromEntries(
  Object.entries(SUB_TAB_SLUG).map(([subTab, slug]) => [slug, subTab as AdminSubTab]),
) as Record<string, AdminSubTab>;

const LEGACY_TAB_WARNED = new Set<LegacyAdminTab>();

const LEGACY_TAB_TO_NAV: Record<LegacyAdminTab, AdminNavState> = {
  knowledge: { section: "knowledge", subTab: "documents" },
  guidelines: { section: "knowledge", subTab: "guidelines" },
  skills: { section: "knowledge", subTab: "behaviors" },
  agents: { section: "agents", subTab: "specialization" },
  simulate: { section: "agents", subTab: "simulation" },
  metrics: { section: "quality", subTab: "metrics" },
  evaluations: { section: "quality", subTab: "evaluations" },
  tools: { section: "platform", subTab: "tools" },
  security: { section: "governance", subTab: "security" },
  audit: { section: "governance", subTab: "audit" },
};

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isAdminAgentRouteId(value: string): boolean {
  return UUID_RE.test(value.trim());
}

export function getAdminSectionConfig(section: AdminSection): AdminSectionConfig {
  const found = ADMIN_SECTIONS.find((item) => item.key === section);

  return found ?? ADMIN_SECTIONS[0];
}

export function getDefaultSubTab(section: AdminSection): AdminSubTab | null {
  return getAdminSectionConfig(section).subTabs[0]?.key ?? null;
}

export function normalizeAdminNav(
  partial: Partial<AdminNavState> | null | undefined,
): AdminNavState {
  const section = partial?.section ?? "overview";
  const config = getAdminSectionConfig(section);
  const subTab = partial?.subTab ?? config.subTabs[0]?.key ?? null;

  return {
    section,
    subTab: config.subTabs.length ? subTab : null,
    agentId: partial?.agentId ?? null,
  };
}

export function legacyTabToNav(tab: LegacyAdminTab, agentId?: string | null): AdminNavState {
  if (import.meta.env.DEV && !LEGACY_TAB_WARNED.has(tab)) {
    LEGACY_TAB_WARNED.add(tab);
    console.warn(
      `[minha-delpi-chat] Aba admin legada "${tab}" foi remapeada para a navegação em seções. ` +
        "Prefira URLs como /admin/conhecimento/documentos.",
    );
  }

  const base = LEGACY_TAB_TO_NAV[tab];

  return normalizeAdminNav({
    ...base,
    agentId: tab === "agents" ? agentId ?? base.agentId : base.agentId,
  });
}

export function parseAdminRouteSegments(segments: string[]): AdminNavState | { agentId: string } {
  if (segments.length === 0) {
    return { section: "overview", subTab: null };
  }

  const [area, second, third] = segments.map((segment) => decodeURIComponent(segment));

  if (area === "agentes") {
    if (second && isAdminAgentRouteId(second)) {
      return { agentId: second };
    }

    const subTab = SUB_TAB_BY_SLUG[second] ?? "specialization";
    const agentId = third && isAdminAgentRouteId(third) ? third : null;

    return normalizeAdminNav({
      section: "agents",
      subTab: subTab === "simulation" || subTab === "specialization" ? subTab : "specialization",
      agentId,
    });
  }

  const section = SECTION_BY_SLUG[area];

  if (!section) {
    return { section: "overview", subTab: null };
  }

  const subTab = second ? SUB_TAB_BY_SLUG[second] ?? null : getDefaultSubTab(section);

  return normalizeAdminNav({ section, subTab });
}

export function buildAdminHref(nav: Partial<AdminNavState>): string {
  const normalized = normalizeAdminNav(nav);
  const base = `${CHAT_BASE_PATH}/admin`;

  if (normalized.section === "overview") {
    return base;
  }

  const sectionSlug = SECTION_SLUG[normalized.section];

  if (normalized.section === "agents" && normalized.agentId && isAdminAgentRouteId(normalized.agentId)) {
    const subSlug = normalized.subTab ? SUB_TAB_SLUG[normalized.subTab] : "especializacao";

    return `${base}/agentes/${subSlug}/${encodeURIComponent(normalized.agentId)}`;
  }

  if (!normalized.subTab) {
    return `${base}/${sectionSlug}`;
  }

  return `${base}/${sectionSlug}/${SUB_TAB_SLUG[normalized.subTab]}`;
}

export function adminNavPanelKey(nav: AdminNavState): string {
  return [nav.section, nav.subTab ?? "", nav.agentId ?? ""].join(":");
}
