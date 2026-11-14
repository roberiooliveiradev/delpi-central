import type { ReactNode } from "react";

import type { LucideIcon } from "lucide-react";
import {
  Ban,
  CheckCircle2,
  FileSearch,
  MessageCircleQuestion,
  Pencil,
  Play,
  RotateCcw,
  Send,
  Undo2,
} from "lucide-react";

import type { PrcInformationQuestionInput } from "../api/productRegistrationApi";

/** Extras repassados pela barra ao `runAction` do detalhe. */
export type PrcCorrectionTargetInput = {
  targetType: "FIELD" | "SUPPLIER_LINK";
  targetPath?: string | null;
  targetAttribute?: string | null;
  supplierKey?: { supplierCode: string; store: string } | null;
  reason: string;
};

export type PrcActionExtras = {
  reason?: string;
  officialCode?: string;
  /** PRC-REF-019 — perguntas tipadas de `request_information`. */
  questions?: PrcInformationQuestionInput[];
  message?: string;
  pendingFields?: string[];
  /** PRC-REF-022 — alvos da devolução. */
  targets?: PrcCorrectionTargetInput[];
};

/** Catálogo de apresentação das ações PRC — disponibilidade real vem
 * sempre de `allowedActions` do backend; aqui só rótulos/exigências. */
export type PrcActionSpec = {
  action: string;
  label: string;
  path: string;
  needsReason?: boolean;
  reasonLabel?: string;
  needsOfficialCode?: boolean;
  /** Abre o formulário multi-pergunta (PrcRequestInformationModal). */
  needsQuestions?: boolean;
  /** PRC-REF-022 — seleção de campos + motivo (PrcReturnForCorrectionModal). */
  needsCorrectionTargets?: boolean;
  confirmTitle?: string;
  confirmMessage?: ReactNode;
  danger?: boolean;
  primary?: boolean;
  /** Ícone Lucide ao lado do rótulo (UX V3 — ação sempre rotulada). */
  icon?: LucideIcon;
  /** Ajuda contextual (title) quando a consequência não é evidente. */
  help?: string;
};

export const PRC_ACTION_SPECS: Record<string, PrcActionSpec> = {
  start: {
    action: "start",
    label: "Iniciar atendimento",
    icon: Play,
    help: "Assume o atendimento desta solicitação.",
    path: "start",
    primary: true,
  },
  edit_draft: {
    action: "edit_draft",
    label: "Editar ficha técnica",
    icon: Pencil,
    help: "Abre a ficha técnica para edição dos campos permitidos.",
    path: "",
    primary: true,
  },
  request_information: {
    action: "request_information",
    label: "Solicitar informações (legado)",
    icon: MessageCircleQuestion,
    help: "Fluxo legado de esclarecimentos — prefira Devolver para correção.",
    path: "request-information",
    needsQuestions: true,
    confirmTitle: "Solicitar informações (legado)",
    confirmMessage:
      "Fluxo legado REF-019. Prefira Devolver para correção.",
  },
  return_for_correction: {
    action: "return_for_correction",
    label: "Devolver para correção",
    icon: Undo2,
    help: "Devolve ao solicitante os campos que precisam de correção.",
    path: "return-for-correction",
    needsCorrectionTargets: true,
    confirmTitle: "Devolver para correção",
    confirmMessage:
      "O solicitante corrigirá na própria ficha os campos indicados e poderá reenviar à Engenharia.",
  },
  resubmit_correction: {
    action: "resubmit_correction",
    label: "Reenviar para Engenharia",
    icon: Send,
    help: "Reenvia a solicitação corrigida para a Engenharia.",
    path: "resubmit-correction",
    confirmTitle: "Reenviar para Engenharia",
    confirmMessage:
      "A solicitação volta para Em atendimento com as correções registradas.",
    primary: true,
  },
  resume: {
    action: "resume",
    label: "Retomar atendimento",
    icon: Play,
    help: "Retoma o atendimento desta solicitação.",
    path: "resume",
    primary: true,
  },
  /** PRC-REF-020 — ação principal de conclusão com verificação oficial. */
  complete: {
    action: "complete",
    label: "Concluir atendimento",
    icon: CheckCircle2,
    help: "Verifica o cadastro oficial no TOTVS e conclui somente se tudo corresponder.",
    path: "complete",
    needsOfficialCode: true,
    confirmTitle: "Concluir atendimento",
    confirmMessage:
      "A Engineering API valida a ficha, consulta o cadastro oficial no TOTVS " +
      "em tempo real e só conclui se todos os campos verificáveis corresponderem. " +
      "Qualquer divergência mantém a solicitação Em atendimento.",
    primary: true,
  },
  /** Legado — só aparece se o backend ainda expuser em allowedActions. */
  return_to_attendance: {
    action: "return_to_attendance",
    label: "Reabrir atendimento",
    icon: RotateCcw,
    help: "Retorna a solicitação Em revisão para Em atendimento.",
    path: "return-to-attendance",
    confirmTitle: "Reabrir atendimento",
    confirmMessage:
      "A solicitação legado Em revisão volta para Em atendimento.",
  },
  submit_review: {
    action: "submit_review",
    label: "Encaminhar para revisão",
    icon: FileSearch,
    help: "Ação legada — prefira Concluir atendimento.",
    path: "submit-review",
    confirmTitle: "Encaminhar para revisão",
    confirmMessage:
      "Ação legada. Prefira Concluir atendimento — a verificação oficial " +
      "ocorre na conclusão.",
  },
  reject: {
    action: "reject",
    label: "Rejeitar",
    icon: Ban,
    help: "Encerra a solicitação definitivamente, sem alterar o cadastro no TOTVS.",
    path: "reject",
    needsReason: true,
    reasonLabel: "Motivo da rejeição",
    confirmTitle: "Rejeitar solicitação",
    confirmMessage:
      "A rejeição é definitiva e não altera o cadastro vigente no TOTVS.",
    danger: true,
  },
  /** Alias legado do mesmo use case de `complete`. */
  verify_and_complete: {
    action: "verify_and_complete",
    label: "Concluir atendimento",
    icon: CheckCircle2,
    help: "Verifica o cadastro oficial no TOTVS e conclui somente se tudo corresponder.",
    path: "verify-and-complete",
    needsOfficialCode: true,
    confirmTitle: "Concluir atendimento",
    confirmMessage:
      "A Engineering API relê o cadastro oficial no TOTVS agora. " +
      "A solicitação só será concluída se todos os campos verificáveis " +
      "corresponderem — divergências mantêm o atendimento aberto.",
    primary: true,
  },
};

export const PRC_ACTION_ORDER = [
  "complete",
  "verify_and_complete",
  "resubmit_correction",
  "return_for_correction",
  "return_to_attendance",
  "resume",
  "start",
  "edit_draft",
  "request_information",
  "submit_review",
  "reject",
];

/** Ações que disparam verificação oficial (loading específico na UI). */
export function isPrcCompleteAction(action: string): boolean {
  return action === "complete" || action === "verify_and_complete";
}
