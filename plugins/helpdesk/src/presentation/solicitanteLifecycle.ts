/**
 * Lifecycle cues for the solicitante detail page.
 * H10 Branch B: accept / reject / satisfaction via BFF when capabilities allow;
 * approval (status 10) still bridges to GLPI.
 */

export type SolicitanteLifecycleCueId =
  | "solved_native"
  | "closed_satisfaction"
  | "closed_done"
  | "approval_pending"
  | "solved_needs_glpi"
  | "closed";

export type SolicitanteLifecycleCue = {
  id: SolicitanteLifecycleCueId;
  variant: "default" | "success";
  message: string;
  ctaLabel?: string;
  showNativeActions?: boolean;
  showSatisfactionForm?: boolean;
};

export function timelineHasSolution(
  timeline: readonly { kind?: string }[] | null | undefined,
): boolean {
  return (timeline ?? []).some((entry) => entry.kind === "solution");
}

export function solicitanteLifecycleCue(input: {
  statusId: number | null | undefined;
  hasSolution: boolean;
  canAcceptSolution?: boolean;
  canRejectSolution?: boolean;
  canSubmitSatisfaction?: boolean;
  satisfaction?: number | null;
}): SolicitanteLifecycleCue | null {
  const statusId = input.statusId == null ? null : Number(input.statusId);
  const canAccept = Boolean(input.canAcceptSolution);
  const canReject = Boolean(input.canRejectSolution);
  const canSat = Boolean(input.canSubmitSatisfaction);

  if (statusId === 6) {
    if (canSat) {
      return {
        id: "closed_satisfaction",
        variant: "default",
        message: "Chamado fechado. Avalie o atendimento (1 a 5) e, se quiser, deixe um comentário.",
        showSatisfactionForm: true,
      };
    }
    if (input.satisfaction != null) {
      return {
        id: "closed_done",
        variant: "success",
        message: `Chamado fechado. Sua avaliação: ${input.satisfaction}/5.`,
      };
    }
    return {
      id: "closed",
      variant: "default",
      message:
        "Este chamado está fechado. Não dá para responder por aqui. Se precisar reabrir, use o helpdesk.",
      ctaLabel: "Abrir no helpdesk",
    };
  }

  if (canAccept || canReject) {
    return {
      id: "solved_native",
      variant: "success",
      message: "Há uma solução neste chamado. Você pode aceitar (fecha) ou recusar (reabre) por aqui.",
      showNativeActions: true,
    };
  }

  if (statusId === 5 || input.hasSolution) {
    return {
      id: "solved_needs_glpi",
      variant: "success",
      message:
        "Há uma solução neste chamado. Aprovar ou recusar ainda não está disponível nesta sessão — abra no helpdesk se precisar concluir.",
      ctaLabel: "Abrir no helpdesk para concluir",
    };
  }

  if (statusId === 10) {
    return {
      id: "approval_pending",
      variant: "default",
      message:
        "Este chamado aguarda aprovação. Você acompanha aqui; se precisar agir no fluxo de aprovação do helpdesk, abra o chamado lá.",
      ctaLabel: "Abrir no helpdesk",
    };
  }
  return null;
}
