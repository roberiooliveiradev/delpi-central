export const PROJECT_ICON_OPTIONS = [
  "folder",
  "bar-chart-3",
  "factory",
  "microscope",
  "badge-check",
  "target",
  "package",
  "lightbulb",
  "wrench",
  "clipboard-list",
] as const;

export type ProjectIconName = (typeof PROJECT_ICON_OPTIONS)[number];

export const DEFAULT_PROJECT_ICON: ProjectIconName = "folder";

export const PROJECT_ICON_LABELS: Record<ProjectIconName, string> = {
  folder: "Pasta",
  "bar-chart-3": "Gráfico",
  factory: "Fábrica",
  microscope: "Laboratório",
  "badge-check": "Qualidade",
  target: "Meta",
  package: "Produto",
  lightbulb: "Ideia",
  wrench: "Manutenção",
  "clipboard-list": "Checklist",
};

const LEGACY_EMOJI_TO_ICON: Record<string, ProjectIconName> = {
  "📁": "folder",
  "📊": "bar-chart-3",
  "🏭": "factory",
  "🔬": "microscope",
  "✅": "badge-check",
  "🎯": "target",
  "📦": "package",
  "💡": "lightbulb",
  "🛠️": "wrench",
  "📋": "clipboard-list",
};

export function isProjectIconName(value: string): value is ProjectIconName {
  return (PROJECT_ICON_OPTIONS as readonly string[]).includes(value);
}

export function normalizeProjectIcon(icon: string | null | undefined): ProjectIconName {
  const trimmed = String(icon ?? "").trim();

  if (!trimmed) {
    return DEFAULT_PROJECT_ICON;
  }

  const legacy = LEGACY_EMOJI_TO_ICON[trimmed];

  if (legacy) {
    return legacy;
  }

  const normalized = trimmed.toLowerCase();

  if (isProjectIconName(normalized)) {
    return normalized;
  }

  return DEFAULT_PROJECT_ICON;
}
