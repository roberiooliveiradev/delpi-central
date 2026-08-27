export const CIPA_STATUS_LABELS: Record<string, string> = {
  draft: "Rascunho",
  in_review: "Em revisão",
  awaiting_signatures: "Aguardando assinaturas",
  partially_signed: "Parcialmente assinada",
  signed: "Assinada",
  finalized: "Finalizada",
  cancelled: "Cancelada",
};

export const CIPA_PARTICIPANT_ROLE_LABELS: Record<string, string> = {
  president: "Presidente da CIPA",
  vice_president: "Vice-presidente da CIPA",
  secretary: "Secretário(a) da CIPA",
  titular_member: "Membro titular",
  alternate_member: "Membro suplente",
  guest: "Convidado(a)",
  action_owner: "Responsável por ação",
  other: "Outro",
};

export const CIPA_UNIT_LABELS: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

export function cipaSignatureStatusLabel(value: unknown): string {
  const status = String(value || "");
  const labels: Record<string, string> = {
    pending: "Pendente",
    viewed: "Visualizada",
    signed: "Assinada",
    refused: "Recusada",
    invalidated: "Invalidada",
  };
  return labels[status] || status;
}
