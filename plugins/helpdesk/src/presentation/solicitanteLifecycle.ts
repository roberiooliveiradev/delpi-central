/**
 * Lifecycle cues for the solicitante detail page.
 * Approve / reject / reopen / satisfaction stay in GLPI (HLAPI CONSOLE) — we only guide.
 */

export type SolicitanteLifecycleCueId = "solved_needs_glpi" | "closed" | "approval_pending";

export type SolicitanteLifecycleCue = {
  id: SolicitanteLifecycleCueId;
  variant: "default" | "success";
  message: string;
  ctaLabel: string;
};

export function timelineHasSolution(
  timeline: readonly { kind?: string }[] | null | undefined,
): boolean {
  return (timeline ?? []).some((entry) => entry.kind === "solution");
}

export function solicitanteLifecycleCue(input: {
  statusId: number | null | undefined;
  hasSolution: boolean;
}): SolicitanteLifecycleCue | null {
  const statusId = input.statusId == null ? null : Number(input.statusId);
  if (statusId === 6) {
    return {
      id: "closed",
      variant: "default",
      message:
        "Este chamado está fechado. Não dá para responder por aqui. Se precisar reabrir ou ver a pesquisa de satisfação, use o helpdesk.",
      ctaLabel: "Abrir no helpdesk",
    };
  }
  if (statusId === 5 || input.hasSolution) {
    return {
      id: "solved_needs_glpi",
      variant: "success",
      message:
        "Há uma solução neste chamado. Aprovar, recusar ou responder a pesquisa ainda é feito no helpdesk — a API nova ainda não entrega esses passos ao solicitante.",
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
