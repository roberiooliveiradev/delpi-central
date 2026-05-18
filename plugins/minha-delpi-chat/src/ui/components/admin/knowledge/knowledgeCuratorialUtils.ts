const SOURCE_TYPE_LABELS: Record<string, string> = {
  diretriz: "Diretriz",
  glossario: "Glossário",
  manual: "Manual",
  politica: "Política",
  admin_upload: "Upload admin",
};

export function formatSourceTypeLabel(sourceType: string): string {
  return SOURCE_TYPE_LABELS[sourceType] ?? sourceType;
}

export function sourceTypeBadgeClass(sourceType: string): string {
  const normalized = sourceType.trim().toLowerCase();

  if (normalized === "diretriz" || normalized === "politica") {
    return "mdc-knowledge-badge--policy";
  }

  if (normalized === "glossario") {
    return "mdc-knowledge-badge--glossary";
  }

  if (normalized === "manual") {
    return "mdc-knowledge-badge--manual";
  }

  return "mdc-knowledge-badge--default";
}
