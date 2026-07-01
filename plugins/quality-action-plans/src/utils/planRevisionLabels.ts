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

export function revisionScopeLabel(scope: string | null | undefined): string {
  const key = (scope || "").trim();
  return REVISION_SCOPE_LABELS[key] ?? (key || "Atualização");
}
