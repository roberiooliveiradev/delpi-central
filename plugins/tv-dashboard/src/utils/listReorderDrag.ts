export type ListDropEdge = "before" | "after";

export type ListDropHint = {
  id: string;
  edge: ListDropEdge;
};

/** Metade superior = inserir antes; inferior = depois. */
export function resolveListDropEdge(clientY: number, rect: Pick<DOMRect, "top" | "height">): ListDropEdge {
  return clientY < rect.top + rect.height / 2 ? "before" : "after";
}

export function listDropHintClassName(hint: ListDropHint | null, id: string): string {
  if (!hint || hint.id !== id) return "";
  return hint.edge === "before" ? "td-reorder--drop-before" : "td-reorder--drop-after";
}

/**
 * Ghost elevado para HTML5 DnD (snapshot do browser).
 * Remove o clone no próximo frame — o motor de drag já capturou a imagem.
 */
export function attachListDragGhost(
  event: { dataTransfer: DataTransfer | null; currentTarget: EventTarget; clientX: number; clientY: number },
): void {
  const transfer = event.dataTransfer;
  const source = event.currentTarget;
  if (!transfer || !(source instanceof HTMLElement)) return;
  transfer.effectAllowed = "move";
  transfer.setData("text/plain", source.dataset.reorderId ?? "");

  const ghost = source.cloneNode(true) as HTMLElement;
  ghost.classList.add("td-reorder-ghost");
  ghost.setAttribute("aria-hidden", "true");
  const width = source.offsetWidth;
  ghost.style.position = "fixed";
  ghost.style.top = "-1200px";
  ghost.style.left = "0";
  ghost.style.width = `${width}px`;
  ghost.style.margin = "0";
  ghost.style.pointerEvents = "none";
  ghost.style.zIndex = "2147483646";
  document.body.appendChild(ghost);

  const rect = source.getBoundingClientRect();
  const offsetX = Math.max(12, Math.min(width - 12, event.clientX - rect.left));
  const offsetY = Math.max(8, Math.min(source.offsetHeight - 8, event.clientY - rect.top));
  transfer.setDragImage(ghost, offsetX, offsetY);
  requestAnimationFrame(() => {
    ghost.remove();
  });
}
