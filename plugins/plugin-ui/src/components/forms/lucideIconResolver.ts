import * as LucideIcons from "lucide-react";
import type { LucideIcon } from "lucide-react";

const iconCache = new Map<string, LucideIcon | null>();

export function toPascalCaseFromKebab(kebab: string): string {
  return kebab
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
}

export function toKebabCase(name: string): string {
  return name
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/([A-Za-z])([0-9])/g, "$1-$2")
    .replace(/_/g, "-")
    .toLowerCase();
}

/**
 * Export PascalCase “canônico” do lucide-react
 * (exclui aliases `*Icon` e prefixo `Lucide*`).
 */
export function isPascalCaseLucideExport(name: string): boolean {
  return (
    /^[A-Z][A-Za-z0-9]*$/.test(name) &&
    !name.endsWith("Icon") &&
    !name.startsWith("Lucide")
  );
}

/** Lista completa de ícones Lucide em PascalCase (sem aliases). */
export function listLucideIconNames(): string[] {
  return Object.keys(LucideIcons)
    .filter(isPascalCaseLucideExport)
    .filter((name) => {
      const value = (LucideIcons as Record<string, unknown>)[name];
      return typeof value === "function" || (typeof value === "object" && value !== null);
    })
    .sort((a, b) => a.localeCompare(b));
}

export function resolveLucideIcon(iconName?: string | null): LucideIcon | null {
  const normalized = String(iconName ?? "")
    .trim()
    .toLowerCase();

  if (!normalized) {
    return null;
  }

  if (iconCache.has(normalized)) {
    return iconCache.get(normalized) ?? null;
  }

  const withoutIconSuffix = normalized.endsWith("-icon")
    ? normalized.slice(0, -"-icon".length)
    : normalized;

  const pascal = withoutIconSuffix.includes("-")
    ? toPascalCaseFromKebab(withoutIconSuffix)
    : withoutIconSuffix.charAt(0).toUpperCase() + withoutIconSuffix.slice(1);

  const component =
    (LucideIcons as unknown as Record<string, LucideIcon | undefined>)[pascal] ?? null;

  iconCache.set(normalized, component);
  return component;
}

export function isLucideIconName(iconName?: string | null): boolean {
  return resolveLucideIcon(iconName) !== null;
}

/**
 * Catálogo curado para formulários / experiência do cliente (kebab-case).
 * Mantém o picker leve e alinhado a casos de uso de negócio.
 */
export const CURATED_LUCIDE_ICON_NAMES = [
  "eye",
  "heart",
  "star",
  "smile",
  "thumbs-up",
  "thumbs-down",
  "handshake",
  "users",
  "user",
  "user-round",
  "building-2",
  "factory",
  "map-pin",
  "globe",
  "clipboard-list",
  "clipboard-check",
  "check-circle-2",
  "circle-alert",
  "triangle-alert",
  "info",
  "search",
  "message-circle",
  "mail",
  "phone",
  "calendar",
  "clock",
  "award",
  "shield-check",
  "sparkles",
  "lightbulb",
  "target",
  "trending-up",
  "bar-chart-3",
  "line-chart",
  "package",
  "truck",
  "wrench",
  "settings",
  "sliders-horizontal",
  "file-text",
  "folder-open",
  "image",
  "camera",
  "headphones",
  "megaphone",
  "flag",
  "bookmark",
  "coffee",
  "leaf",
  "sun",
  "moon",
  "zap",
] as const;

export type CuratedLucideIconName = (typeof CURATED_LUCIDE_ICON_NAMES)[number];

export type LucideIconSectionDef = {
  id: string;
  label: string;
  /** Nomes em kebab-case. */
  icons: readonly string[];
};

/** Seções do picker — ícones podem aparecer em mais de uma seção. */
export const LUCIDE_ICON_SECTIONS: readonly LucideIconSectionDef[] = [
  {
    id: "featured",
    label: "Em destaque",
    icons: [
      "eye",
      "heart",
      "star",
      "smile",
      "thumbs-up",
      "handshake",
      "sparkles",
      "lightbulb",
      "award",
      "flag",
    ],
  },
  {
    id: "people",
    label: "Pessoas e equipe",
    icons: [
      "user",
      "user-round",
      "users",
      "user-check",
      "user-plus",
      "user-cog",
      "contact",
      "handshake",
      "accessibility",
      "baby",
    ],
  },
  {
    id: "feedback",
    label: "Feedback e emoção",
    icons: [
      "heart",
      "heart-handshake",
      "smile",
      "laugh",
      "frown",
      "meh",
      "thumbs-up",
      "thumbs-down",
      "message-circle",
      "message-square",
      "party-popper",
      "hand-heart",
    ],
  },
  {
    id: "communication",
    label: "Comunicação",
    icons: [
      "mail",
      "phone",
      "phone-call",
      "megaphone",
      "bell",
      "send",
      "inbox",
      "at-sign",
      "headphones",
      "video",
      "mic",
    ],
  },
  {
    id: "place",
    label: "Local e empresa",
    icons: [
      "map-pin",
      "map",
      "globe",
      "building-2",
      "building",
      "factory",
      "home",
      "store",
      "landmark",
      "navigation",
    ],
  },
  {
    id: "work",
    label: "Trabalho e qualidade",
    icons: [
      "clipboard-list",
      "clipboard-check",
      "check-circle-2",
      "circle-check",
      "list-checks",
      "file-check",
      "badge-check",
      "shield-check",
      "target",
      "goal",
      "briefcase",
      "hammer",
      "wrench",
    ],
  },
  {
    id: "alerts",
    label: "Alertas e info",
    icons: [
      "info",
      "circle-alert",
      "triangle-alert",
      "octagon-alert",
      "circle-help",
      "help-circle",
      "ban",
      "shield-alert",
      "siren",
    ],
  },
  {
    id: "time",
    label: "Tempo e agenda",
    icons: [
      "calendar",
      "calendar-check",
      "calendar-days",
      "clock",
      "timer",
      "hourglass",
      "history",
      "alarm-clock",
      "sunrise",
      "sunset",
    ],
  },
  {
    id: "data",
    label: "Dados e tendência",
    icons: [
      "bar-chart-3",
      "line-chart",
      "pie-chart",
      "trending-up",
      "trending-down",
      "activity",
      "gauge",
      "percent",
      "hash",
      "calculator",
    ],
  },
  {
    id: "ops",
    label: "Operação e logística",
    icons: [
      "package",
      "package-check",
      "truck",
      "forklift",
      "warehouse",
      "boxes",
      "container",
      "ship",
      "plane",
      "route",
    ],
  },
  {
    id: "media",
    label: "Mídia e arquivos",
    icons: [
      "image",
      "images",
      "camera",
      "film",
      "file-text",
      "file",
      "files",
      "folder-open",
      "folder",
      "paperclip",
      "download",
      "upload",
      "printer",
    ],
  },
  {
    id: "system",
    label: "Sistema e ajustes",
    icons: [
      "settings",
      "sliders-horizontal",
      "sliders-vertical",
      "cog",
      "search",
      "filter",
      "funnel",
      "menu",
      "layout-dashboard",
      "panels-top-left",
      "lock",
      "key",
      "power",
    ],
  },
  {
    id: "nature",
    label: "Natureza e clima",
    icons: [
      "sun",
      "moon",
      "cloud",
      "cloud-sun",
      "leaf",
      "flower-2",
      "trees",
      "droplets",
      "flame",
      "snowflake",
      "zap",
      "wind",
    ],
  },
  {
    id: "misc",
    label: "Diversos",
    icons: [
      "bookmark",
      "coffee",
      "gift",
      "shopping-cart",
      "shopping-bag",
      "wallet",
      "credit-card",
      "qr-code",
      "scan",
      "tag",
      "tags",
      "pin",
      "link",
      "share-2",
    ],
  },
] as const;

export type LucideIconSectionView = {
  id: string;
  label: string;
  /** PascalCase para render. */
  icons: string[];
};

function existingPascalFromKebab(kebab: string): string | null {
  const pascal = toPascalCaseFromKebab(kebab);
  if ((LucideIcons as Record<string, unknown>)[pascal]) return pascal;
  return null;
}

/**
 * Agrupa ícones em seções.
 * - Sem busca: mostra as seções (ícones declarados que existem no Lucide).
 * - Com busca + `curatedOnly=false`: percorre o catálogo Lucide completo.
 * - Com busca + `curatedOnly=true`: só o catálogo curado.
 */
export function groupLucideIconsBySection(options: {
  curatedOnly?: boolean;
  query?: string;
  maxResults?: number;
}): LucideIconSectionView[] {
  const curatedOnly = options.curatedOnly ?? true;
  const query = String(options.query ?? "")
    .trim()
    .toLowerCase();
  const maxResults = Math.max(1, options.maxResults ?? 480);

  const matchesQuery = (pascal: string): boolean => {
    if (!query) return true;
    const kebab = toKebabCase(pascal);
    return kebab.includes(query) || pascal.toLowerCase().includes(query);
  };

  const searchPool = (() => {
    if (!query) {
      const fromSections = new Set<string>();
      for (const section of LUCIDE_ICON_SECTIONS) {
        for (const kebab of section.icons) {
          const pascal = existingPascalFromKebab(kebab);
          if (pascal) fromSections.add(pascal);
        }
      }
      if (curatedOnly) {
        for (const kebab of CURATED_LUCIDE_ICON_NAMES) {
          const pascal = existingPascalFromKebab(kebab);
          if (pascal) fromSections.add(pascal);
        }
      }
      return Array.from(fromSections).sort((a, b) => a.localeCompare(b));
    }
    if (curatedOnly) {
      return CURATED_LUCIDE_ICON_NAMES.map((kebab) => existingPascalFromKebab(kebab))
        .filter((name): name is string => Boolean(name))
        .filter(matchesQuery);
    }
    return listLucideIconNames().filter(matchesQuery).slice(0, maxResults);
  })();

  const filteredSet = new Set(searchPool);
  const placed = new Set<string>();
  const sections: LucideIconSectionView[] = [];

  for (const section of LUCIDE_ICON_SECTIONS) {
    const icons: string[] = [];
    for (const kebab of section.icons) {
      const pascal = existingPascalFromKebab(kebab);
      if (!pascal || !filteredSet.has(pascal) || placed.has(pascal)) continue;
      icons.push(pascal);
      placed.add(pascal);
    }
    if (icons.length > 0) {
      sections.push({ id: section.id, label: section.label, icons });
    }
  }

  const remaining = searchPool.filter((pascal) => !placed.has(pascal));
  if (remaining.length > 0) {
    sections.push({
      id: query ? "results" : "other",
      label: query ? "Outros resultados" : "Outros",
      icons: remaining,
    });
  }

  return sections;
}

export function countGroupedLucideIcons(sections: LucideIconSectionView[]): number {
  return sections.reduce((sum, section) => sum + section.icons.length, 0);
}

export function countLucideCatalogSize(): number {
  return listLucideIconNames().length;
}
