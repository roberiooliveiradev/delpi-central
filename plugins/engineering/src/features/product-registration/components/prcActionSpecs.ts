import type { ReactNode } from "react";

/** Catálogo de apresentação das ações PRC — disponibilidade real vem
 * sempre de `allowedActions` do backend; aqui só rótulos/exigências. */
export type PrcActionSpec = {
  action: string;
  label: string;
  path: string;
  needsReason?: boolean;
  reasonLabel?: string;
  needsOfficialCode?: boolean;
  confirmTitle?: string;
  confirmMessage?: ReactNode;
  danger?: boolean;
  primary?: boolean;
};

export const PRC_ACTION_SPECS: Record<string, PrcActionSpec> = {
  start: {
    action: "start",
    label: "Iniciar atendimento",
    path: "start",
    primary: true,
  },
  edit_draft: {
    action: "edit_draft",
    label: "Editar ficha técnica",
    path: "",
    primary: true,
  },
  request_information: {
    action: "request_information",
    label: "Solicitar informações",
    path: "request-information",
    needsReason: true,
    reasonLabel: "Motivo da pendência",
    confirmTitle: "Solicitar informações",
    confirmMessage:
      "A solicitação ficará aguardando informações até ser retomada.",
  },
  resume: {
    action: "resume",
    label: "Retomar atendimento",
    path: "resume",
    primary: true,
  },
  submit_review: {
    action: "submit_review",
    label: "Encaminhar para revisão",
    path: "submit-review",
    primary: true,
    confirmTitle: "Encaminhar para revisão",
    confirmMessage:
      "A ficha técnica será congelada para avaliação e verificação oficial.",
  },
  reject: {
    action: "reject",
    label: "Rejeitar",
    path: "reject",
    needsReason: true,
    reasonLabel: "Motivo da rejeição",
    confirmTitle: "Rejeitar solicitação",
    confirmMessage:
      "A rejeição é definitiva e não altera o cadastro vigente no TOTVS.",
    danger: true,
  },
  verify_and_complete: {
    action: "verify_and_complete",
    label: "Verificar e concluir",
    path: "verify-and-complete",
    needsOfficialCode: true,
    confirmTitle: "Verificar e concluir",
    confirmMessage:
      "A Engineering API relê o cadastro oficial no TOTVS agora. " +
      "A solicitação só será concluída se todos os campos verificáveis " +
      "corresponderem — divergências mantêm a revisão em aberto.",
    primary: true,
  },
};

export const PRC_ACTION_ORDER = [
  "verify_and_complete",
  "submit_review",
  "resume",
  "start",
  "edit_draft",
  "request_information",
  "reject",
];
