export const STATUS_LABELS: Record<string, string> = {
  draft: "Rascunho",
  in_review: "Em revisão",
  awaiting_signatures: "Aguardando assinaturas",
  partially_signed: "Parcialmente assinada",
  signed: "Assinada",
  finalized: "Finalizada",
  cancelled: "Cancelada",
};

export const MEETING_TYPE_LABELS: Record<string, string> = {
  ordinary: "Ordinária",
  extraordinary: "Extraordinária",
  other: "Outro",
};

export const PARTICIPANT_ROLE_LABELS: Record<string, string> = {
  president: "Presidente",
  secretary: "Secretário(a)",
  member: "Membro",
  guest: "Convidado(a)",
  other: "Outro",
  vice_president: "Vice-presidente",
  titular_member: "Membro",
  alternate_member: "Membro",
};

/** Cargos do cadastro permanente do Comitê. */
export const MEMBER_ROLE_LABELS: Record<string, string> = {
  president: PARTICIPANT_ROLE_LABELS.president,
  secretary: PARTICIPANT_ROLE_LABELS.secretary,
  member: PARTICIPANT_ROLE_LABELS.member,
  guest: PARTICIPANT_ROLE_LABELS.guest,
};

export const MEMBER_ROLE_OPTIONS = Object.entries(MEMBER_ROLE_LABELS).map(
  ([value, label]) => ({ value, label }),
);

export const UNIT_LABELS: Record<string, string> = {
  "00": "Comitê de Ética e Conduta",
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

export const HISTORY_ACTION_LABELS: Record<string, string> = {
  create: "Criação",
  update: "Atualização",
  edit: "Edição",
  replace_participants: "Participantes atualizados",
  replace_signers: "Signatários atualizados",
  send_for_signature: "Enviada para assinatura",
  signature_progress: "Progresso de assinaturas",
  signature_refused: "Assinatura recusada",
  refuse_signature: "Assinatura recusada",
  sign: "Assinatura",
  finalize: "Finalização",
  cancel: "Cancelamento",
  soft_delete: "Exclusão",
  create_version: "Nova versão",
};

/** Ações da trilha de auditoria da ata. */
export const AUDIT_ACTION_LABELS: Record<string, string> = {
  create: "Ata criada",
  edit: "Dados da ata editados",
  edit_content: "Conteúdo editado",
  replace_participants: "Participantes atualizados",
  replace_signers: "Signatários atualizados",
  send_for_signature: "Enviada para assinatura",
  sign: "Assinatura registrada",
  signature_progress: "Progresso de assinaturas",
  refuse_signature: "Assinatura recusada",
  create_version: "Nova versão criada",
  finalize: "Ata finalizada",
  cancel: "Ata cancelada",
  soft_delete: "Ata excluída",
};
