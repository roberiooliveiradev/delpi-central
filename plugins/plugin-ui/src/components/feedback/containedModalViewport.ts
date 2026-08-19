import type { CSSProperties } from "react";

/**
 * Viewport do modal contido no MFE.
 *
 * O root `.dashboard-*` tem `height: auto` (altura = conteúdo) no portal — ver
 * `.app-host-federated__mount:has(.dashboard-page…)` em `portal/src/index.css`.
 * Overlay `absolute; inset: 0` nesse host fica maior que a tela (página longa)
 * ou desalinhado. A caixa visível é o scrollport (`.content` / overflow),
 * não a altura do documento do MFE.
 */

export type ContainedModalBox = {
  top: number;
  left: number;
  width: number;
  height: number;
};

function isScrollableOverflow(value: string): boolean {
  return value === "auto" || value === "scroll" || value === "overlay";
}

/** Scrollport mais próximo (ex.: `.content` do portal) ou o próprio host. */
export function resolveContainedModalScrollPort(host: HTMLElement): HTMLElement {
  let node: HTMLElement | null = host.parentElement;
  while (node && node !== document.documentElement) {
    if (node.classList.contains("content")) {
      return node;
    }
    const style = getComputedStyle(node);
    if (
      (isScrollableOverflow(style.overflowY) || isScrollableOverflow(style.overflow)) &&
      node.clientHeight > 0
    ) {
      return node;
    }
    node = node.parentElement;
  }

  const content = document.querySelector<HTMLElement>(".content");
  if (content?.clientHeight) {
    return content;
  }
  return host;
}

function intersectVisibleBoxes(
  hostRect: DOMRect,
  portRect: DOMRect,
): ContainedModalBox {
  const top = Math.max(hostRect.top, portRect.top);
  const left = Math.max(hostRect.left, portRect.left);
  const right = Math.min(hostRect.right, portRect.right);
  const bottom = Math.min(hostRect.bottom, portRect.bottom);
  return {
    top: Math.max(0, top),
    left: Math.max(0, left),
    width: Math.max(0, right - left),
    height: Math.max(0, bottom - top),
  };
}

/**
 * Caixa visível do overlay: interseção do host com o scrollport.
 * Página MFE alta recorta no `.content`; host menor (ex.: lista da conversa)
 * permanece na coluna — não estica até a borda direita do portal.
 */
export function measureContainedModalBox(host: HTMLElement): ContainedModalBox {
  const scrollPort = resolveContainedModalScrollPort(host);
  return intersectVisibleBoxes(
    host.getBoundingClientRect(),
    scrollPort.getBoundingClientRect(),
  );
}

export function containedModalBoxToStyle(box: ContainedModalBox): CSSProperties {
  // Não usar shorthand `inset` aqui: em React/CSS ele zera top/left depois
  // de setá-los → fixed sem âncora cai na posição estática (modal “embaixo”).
  return {
    position: "fixed",
    top: box.top,
    left: box.left,
    width: box.width,
    height: box.height,
    right: "auto",
    bottom: "auto",
    minWidth: 0,
    minHeight: 0,
  };
}

/** Trava o scroll do scrollport (e body) enquanto o modal contido está aberto. */
export function lockContainedModalScroll(host: HTMLElement): () => void {
  const scrollPort = resolveContainedModalScrollPort(host);
  const previousPortOverflow = scrollPort.style.overflow;
  const previousBodyOverflow = document.body.style.overflow;
  scrollPort.style.overflow = "hidden";
  document.body.style.overflow = "hidden";
  return () => {
    scrollPort.style.overflow = previousPortOverflow;
    document.body.style.overflow = previousBodyOverflow;
  };
}
