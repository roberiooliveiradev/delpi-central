import type { MouseEventHandler } from "react";

import type { DashboardPagePathProps } from "@delpi/plugin-ui/index";

import { PORTAL_PAGE_COPY } from "../constants/portalExperience";
import {
  buildAtaPath,
  TRANSFORMOMETRO_ROUTES,
} from "../constants/routes";

/** Truncate breadcrumb labels — never expose raw UUIDs as the visible crumb. */
export function truncatePathLabel(label: string, max = 42): string {
  const trimmed = label.trim().replace(/\s+/g, " ");
  if (!trimmed) return "…";
  if (trimmed.length <= max) return trimmed;
  return `${trimmed.slice(0, Math.max(1, max - 1))}…`;
}

export function isLikelyUuidLabel(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    value.trim(),
  );
}

export function safeEntityPathLabel(
  preferred: string | null | undefined,
  fallback: string,
): string {
  const raw = String(preferred ?? "").trim();
  if (!raw || isLikelyUuidLabel(raw)) return fallback;
  return truncatePathLabel(raw);
}

type Navigate = (path: string) => void;

function withNavigate(
  href: string,
  label: string,
  onNavigate: Navigate,
): { label: string; href: string; onNavigate: MouseEventHandler<HTMLAnchorElement> } {
  return {
    label,
    href,
    onNavigate: (event) => {
      event.preventDefault();
      onNavigate(href);
    },
  };
}

/** Início → {current} for top-level portal sections. */
export function buildRootSectionPagePath(
  current: string,
  onNavigate: Navigate,
): DashboardPagePathProps {
  return {
    back: withNavigate(TRANSFORMOMETRO_ROUTES.home, "Início", onNavigate),
    items: [],
    current,
    ariaLabel: "Caminho da página",
  };
}

export function buildMeetingMinutesListPagePath(
  onNavigate: Navigate,
): DashboardPagePathProps {
  return buildRootSectionPagePath(PORTAL_PAGE_COPY.meetingMinutes.title, onNavigate);
}

export function buildMeetingMinuteDetailPagePath(options: {
  onNavigate: Navigate;
  label: string;
}): DashboardPagePathProps {
  const atas = TRANSFORMOMETRO_ROUTES.meetingMinutes;
  return {
    back: withNavigate(atas, PORTAL_PAGE_COPY.meetingMinutes.title, options.onNavigate),
    items: [],
    current: safeEntityPathLabel(options.label, "Ata"),
    ariaLabel: "Caminho da ata",
  };
}

export function buildMeetingMinuteEditorPagePath(options: {
  onNavigate: Navigate;
  ataId?: string;
  label?: string | null;
  mode: "new" | "edit";
}): DashboardPagePathProps {
  const atas = TRANSFORMOMETRO_ROUTES.meetingMinutes;
  if (options.mode === "new" || !options.ataId) {
    return {
      back: withNavigate(atas, PORTAL_PAGE_COPY.meetingMinutes.title, options.onNavigate),
      items: [],
      current: "Nova ata",
      ariaLabel: "Caminho da nova ata",
    };
  }
  const detailHref = buildAtaPath(options.ataId);
  const detailLabel = safeEntityPathLabel(options.label, "Ata");
  return {
    back: withNavigate(atas, PORTAL_PAGE_COPY.meetingMinutes.title, options.onNavigate),
    items: [
      {
        id: "minute",
        ...withNavigate(detailHref, detailLabel, options.onNavigate),
      },
    ],
    current: "Editar",
    ariaLabel: "Caminho da edição da ata",
  };
}

export function buildMeetingMinuteSignPagePath(options: {
  onNavigate: Navigate;
  ataId: string;
  label?: string | null;
}): DashboardPagePathProps {
  const atas = TRANSFORMOMETRO_ROUTES.meetingMinutes;
  const detailHref = buildAtaPath(options.ataId);
  const detailLabel = safeEntityPathLabel(options.label, "Ata");
  return {
    back: withNavigate(atas, PORTAL_PAGE_COPY.meetingMinutes.title, options.onNavigate),
    items: [
      {
        id: "minute",
        ...withNavigate(detailHref, detailLabel, options.onNavigate),
      },
    ],
    current: "Assinar",
    ariaLabel: "Caminho da assinatura da ata",
  };
}

export function buildMeetingMinutesPendingPagePath(
  onNavigate: Navigate,
): DashboardPagePathProps {
  const atas = TRANSFORMOMETRO_ROUTES.meetingMinutes;
  return {
    back: withNavigate(atas, PORTAL_PAGE_COPY.meetingMinutes.title, onNavigate),
    items: [],
    current: "Pendências",
    ariaLabel: "Caminho das assinaturas pendentes",
  };
}

export function buildMySignaturePagePath(onNavigate: Navigate): DashboardPagePathProps {
  const atas = TRANSFORMOMETRO_ROUTES.meetingMinutes;
  return {
    back: withNavigate(atas, PORTAL_PAGE_COPY.meetingMinutes.title, onNavigate),
    items: [],
    current: "Minha assinatura",
    ariaLabel: "Caminho da minha assinatura",
  };
}

export type SettingsCatalogSection = "unidades" | "departamentos" | "recursos";

const SETTINGS_SECTION_LABEL: Record<SettingsCatalogSection, string> = {
  unidades: "Unidades",
  departamentos: "Departamentos",
  recursos: "Recursos compartilhados",
};

function settingsSectionHref(section: SettingsCatalogSection): string {
  if (section === "unidades") return TRANSFORMOMETRO_ROUTES.settingsUnits;
  if (section === "departamentos") return TRANSFORMOMETRO_ROUTES.settingsDepartments;
  return TRANSFORMOMETRO_ROUTES.settingsSharedResources;
}

/** Início → Configurações → {section} */
export function buildSettingsSectionPagePath(
  section: SettingsCatalogSection,
  onNavigate: Navigate,
): DashboardPagePathProps {
  const settingsHref = TRANSFORMOMETRO_ROUTES.settingsUnits;
  return {
    back: withNavigate(TRANSFORMOMETRO_ROUTES.home, "Início", onNavigate),
    items: [
      {
        id: "settings",
        ...withNavigate(settingsHref, PORTAL_PAGE_COPY.settings.title, onNavigate),
      },
    ],
    current: SETTINGS_SECTION_LABEL[section],
    ariaLabel: "Caminho das configurações",
  };
}

/** Configurações → {section} → {entity|Nova …} */
export function buildSettingsEntityPagePath(options: {
  section: SettingsCatalogSection;
  onNavigate: Navigate;
  label?: string | null;
  create?: boolean;
}): DashboardPagePathProps {
  const sectionHref = settingsSectionHref(options.section);
  const sectionLabel = SETTINGS_SECTION_LABEL[options.section];
  const createFallback =
    options.section === "unidades"
      ? "Nova unidade"
      : options.section === "departamentos"
        ? "Novo departamento"
        : "Novo recurso";
  const detailFallback =
    options.section === "unidades"
      ? "Unidade"
      : options.section === "departamentos"
        ? "Departamento"
        : "Recurso";
  const current = options.create
    ? createFallback
    : safeEntityPathLabel(options.label, detailFallback);
  return {
    back: withNavigate(
      TRANSFORMOMETRO_ROUTES.settingsUnits,
      PORTAL_PAGE_COPY.settings.title,
      options.onNavigate,
    ),
    items: [
      {
        id: "section",
        ...withNavigate(sectionHref, sectionLabel, options.onNavigate),
      },
    ],
    current,
    ariaLabel: "Caminho do cadastro",
  };
}
