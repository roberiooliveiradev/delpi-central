export const REVISION_SCOPE_LABELS: Record<string, string> = {
  created: "Criação",
  identification: "Identificação",
  status: "Status",
  ishikawa: "Ishikawa",
  five_whys: "5 Porquês",
  rnc_8d: "Relatório 8D",
  actions: "Ações",
  effectiveness: "Eficácia",
  restore: "Restauração",
};

const REVISION_SCOPE_BADGE_CLASS: Record<string, string> = {
  created: "pac-badge--revision-created",
  identification: "pac-badge--revision-identification",
  status: "pac-badge--revision-status",
  ishikawa: "pac-badge--revision-analysis",
  five_whys: "pac-badge--revision-analysis",
  rnc_8d: "pac-badge--revision-rnc8d",
  actions: "pac-badge--revision-actions",
  effectiveness: "pac-badge--revision-effectiveness",
  restore: "pac-badge--revision-restore",
};

export function revisionScopeLabel(scope: string | null | undefined): string {
  const key = (scope || "").trim();
  return REVISION_SCOPE_LABELS[key] ?? (key || "Atualização");
}

export function revisionScopeBadgeClass(scope: string | null | undefined): string {
  const key = (scope || "").trim();
  return REVISION_SCOPE_BADGE_CLASS[key] ?? "pac-badge--revision-default";
}
