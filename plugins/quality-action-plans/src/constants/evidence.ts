export const EVIDENCE_TYPE_OPTIONS = [
  { value: "image", label: "Imagem" },
  { value: "pdf", label: "PDF" },
  { value: "spreadsheet", label: "Planilha" },
  { value: "email", label: "E-mail" },
  { value: "message", label: "Mensagem" },
  { value: "manual_text", label: "Texto" },
  { value: "other", label: "Outro" },
] as const;

export const EVIDENCE_SECTION_OPTIONS = [
  { value: "general", label: "Geral" },
  { value: "nc_description", label: "Descrição NC" },
  { value: "containment", label: "Contenção" },
  { value: "root_cause", label: "Causa raiz" },
  { value: "corrective", label: "Ação corretiva" },
  { value: "effectiveness", label: "Eficácia" },
  { value: "preventive", label: "Preventiva" },
  { value: "documentation", label: "Documentação" },
  { value: "attachments", label: "Anexos (aba evidências)" },
] as const;

const EVIDENCE_TYPE_LABELS = Object.fromEntries(
  EVIDENCE_TYPE_OPTIONS.map((option) => [option.value, option.label]),
) as Record<string, string>;

const EVIDENCE_SECTION_LABELS = Object.fromEntries(
  EVIDENCE_SECTION_OPTIONS.map((option) => [option.value, option.label]),
) as Record<string, string>;

export function evidenceTypeLabel(type: string | null | undefined): string {
  if (!type) return "—";
  return EVIDENCE_TYPE_LABELS[type] ?? type.replace(/_/g, " ");
}

export function evidenceSectionLabel(section: string | null | undefined): string {
  const key = section ?? "general";
  return EVIDENCE_SECTION_LABELS[key] ?? key.replace(/_/g, " ");
}
