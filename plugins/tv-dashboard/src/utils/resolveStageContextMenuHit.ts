/**
 * Resolve o alvo do menu de contexto do palco.
 * Preferência: blockId explícito (handler do wrap) → ancestral `[data-block-id]`.
 */
export function resolveStageContextMenuHit(input: {
  blockId?: string | null;
  eventTarget: EventTarget | null;
}): { type: "block"; blockId: string } | { type: "empty" } {
  const explicit = input.blockId?.trim();
  if (explicit) return { type: "block", blockId: explicit };

  const el =
    input.eventTarget instanceof Element
      ? input.eventTarget
      : input.eventTarget instanceof Node
        ? input.eventTarget.parentElement
        : null;
  const host = el?.closest?.("[data-block-id]");
  const hitId = host?.getAttribute("data-block-id")?.trim();
  if (hitId) return { type: "block", blockId: hitId };
  return { type: "empty" };
}
