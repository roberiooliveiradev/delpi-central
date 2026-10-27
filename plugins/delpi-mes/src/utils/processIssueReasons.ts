/**
 * Catálogo de tipos de problema de processo para o encaminhamento de
 * paradas ao departamento de Processos (Etapa 3).
 *
 * Espelha os códigos canônicos validados pelo Requests API — aqui ficam
 * apenas labels de apresentação; a autoridade de validação é o backend.
 */

export type ProcessIssueReasonOption = { code: string; label: string };

export const PROCESS_ISSUE_REASON_OPTIONS: readonly ProcessIssueReasonOption[] = [
  { code: "work_center_incompatible", label: "CT / posto não adequado" },
  { code: "machine_limitation", label: "Limitação da máquina ou bancada" },
  { code: "tool_not_linked", label: "Ferramenta não informada ou não vinculada" },
  { code: "material_not_linked", label: "Matéria-prima não vinculada à operação" },
  { code: "process_information_missing", label: "Informação de processo incompleta" },
  { code: "other", label: "Outro problema de processo" },
] as const;

export function isProcessIssueReasonCode(code: string | null | undefined): boolean {
  return PROCESS_ISSUE_REASON_OPTIONS.some((item) => item.code === code);
}
