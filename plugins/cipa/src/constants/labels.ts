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
  installation: "Instalação",
  election: "Eleição",
  training: "Treinamento",
  other: "Outro",
};

export const PARTICIPANT_ROLE_LABELS: Record<string, string> = {
  president: "Presidente da CIPA",
  vice_president: "Vice-presidente da CIPA",
  secretary: "Secretário(a) da CIPA",
  titular_member: "Membro titular",
  alternate_member: "Membro suplente",
  guest: "Convidado(a)",
  action_owner: "Responsável por ação",
  other: "Outro",
};

/** Cargos do cadastro permanente da CIPA (subset dos papéis de ata). */
export const MEMBER_ROLE_LABELS: Record<string, string> = {
  president: PARTICIPANT_ROLE_LABELS.president,
  vice_president: PARTICIPANT_ROLE_LABELS.vice_president,
  secretary: PARTICIPANT_ROLE_LABELS.secretary,
  titular_member: PARTICIPANT_ROLE_LABELS.titular_member,
  alternate_member: PARTICIPANT_ROLE_LABELS.alternate_member,
};

export const MEMBER_ROLE_OPTIONS = Object.entries(MEMBER_ROLE_LABELS).map(
  ([value, label]) => ({ value, label }),
);

export const UNIT_LABELS: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

/** Ações da trilha de auditoria da ata (cipa.meeting_minute_audit_logs). */
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
