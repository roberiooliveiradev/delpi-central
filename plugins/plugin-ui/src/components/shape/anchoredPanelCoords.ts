export type AnchoredPanelPlacement = "bottom" | "top" | "right" | "left";

export type AnchoredPanelContainRect = {
  left: number;
  top: number;
  right: number;
  bottom: number;
};

export type AnchoredPanelCoordsInput = {
  anchor: { left: number; top: number; right: number; bottom: number; width: number; height: number };
  panelWidth: number;
  panelHeight: number;
  gap?: number;
  margin?: number;
  viewportWidth: number;
  viewportHeight: number;
  /**
   * Retângulo de contenção (ex.: scroller da thread). Quando informado, o clamp
   * vertical/horizontal respeita esses limites em vez de só o viewport — evita
   * a toolbar invadir header/TopBar fora da área de mensagens.
   */
  containRect?: AnchoredPanelContainRect;
  /** Preferência: usa se couber; senão tenta alternativas e cai para baixo/cima. */
  preferredPlacement?: AnchoredPanelPlacement;
  /**
   * Quando false, `bottom`/`top` não invertem o lado — só clamp no viewport.
   * Útil na ribbon do editor (evita painel subir e cobrir a faixa).
   */
  allowFlip?: boolean;
  /**
   * Alinhamento horizontal em placements `top`/`bottom`.
   * `start` = borda esquerda do âncora; `end` = borda direita (bolhas «mine»).
   * Sempre faz clamp no viewport.
   */
  horizontalAlign?: "start" | "end";
};

export type AnchoredPanelCoords = {
  top: number;
  left: number;
  placement: AnchoredPanelPlacement;
};

function clamp(n: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, n));
}

function spaceRight(anchor: AnchoredPanelCoordsInput["anchor"], gap: number, vw: number): number {
  return vw - anchor.right - gap;
}

function spaceLeft(anchor: AnchoredPanelCoordsInput["anchor"], gap: number): number {
  return anchor.left - gap;
}

/**
 * Posiciona painel ancorado. Com `preferredPlacement: "right"|"left"`, fica ao lado
 * do gatilho quando há espaço; senão usa baixo/cima.
 */
export function resolveAnchoredPanelCoords(input: AnchoredPanelCoordsInput): AnchoredPanelCoords {
  const gap = input.gap ?? 4;
  const margin = input.margin ?? 8;
  const allowFlip = input.allowFlip !== false;
  const horizontalAlign = input.horizontalAlign === "end" ? "end" : "start";
  const { anchor, panelWidth, panelHeight, viewportWidth: vw, viewportHeight: vh } = input;
  const preferred = input.preferredPlacement ?? "bottom";
  const contain = input.containRect;
  const minTop = contain ? Math.max(margin, contain.top + margin) : margin;
  const maxBottom = contain
    ? Math.min(vh - margin, contain.bottom - margin)
    : vh - margin;
  const minLeft = contain ? Math.max(margin, contain.left + margin) : margin;
  const maxRight = contain
    ? Math.min(vw - margin, contain.right - margin)
    : vw - margin;

  const alignVerticalBeside = (): number => {
    if (panelHeight <= 0) return anchor.top;
    return clamp(anchor.top, minTop, Math.max(minTop, maxBottom - panelHeight));
  };

  const alignHorizontalBelow = (): number => {
    if (panelWidth <= 0) {
      return horizontalAlign === "end" ? anchor.right : anchor.left;
    }
    const preferredLeft =
      horizontalAlign === "end" ? anchor.right - panelWidth : anchor.left;
    return clamp(preferredLeft, minLeft, Math.max(minLeft, maxRight - panelWidth));
  };

  const tryRight = (): AnchoredPanelCoords | null => {
    if (panelWidth > 0 && spaceRight(anchor, gap, vw) < panelWidth) return null;
    return {
      placement: "right",
      left: anchor.right + gap,
      top: alignVerticalBeside(),
    };
  };

  const tryLeft = (): AnchoredPanelCoords | null => {
    if (panelWidth > 0 && spaceLeft(anchor, gap) < panelWidth) return null;
    return {
      placement: "left",
      left: anchor.left - panelWidth - gap,
      top: alignVerticalBeside(),
    };
  };

  const tryBottom = (): AnchoredPanelCoords => {
    let top = anchor.bottom + gap;
    if (panelHeight > 0 && top + panelHeight > maxBottom) {
      if (allowFlip) {
        const above = anchor.top - panelHeight - gap;
        top = above >= minTop ? above : Math.max(minTop, maxBottom - panelHeight);
        return { placement: above >= minTop ? "top" : "bottom", left: alignHorizontalBelow(), top };
      }
      top = Math.max(minTop, maxBottom - panelHeight);
    }
    return { placement: "bottom", left: alignHorizontalBelow(), top };
  };

  const tryTop = (): AnchoredPanelCoords => {
    let top = anchor.top - panelHeight - gap;
    if (panelHeight > 0 && top < minTop) {
      if (allowFlip) {
        const below = anchor.bottom + gap;
        const spaceDown = maxBottom - (anchor.bottom + gap);
        const spaceUp = anchor.top - gap - minTop;
        if (below + panelHeight <= maxBottom || spaceDown >= spaceUp) {
          return { placement: "bottom", left: alignHorizontalBelow(), top: below };
        }
      }
      top = minTop;
    }
    return { placement: "top", left: alignHorizontalBelow(), top };
  };

  if (preferred === "right") {
    return tryRight() ?? tryLeft() ?? tryBottom();
  }
  if (preferred === "left") {
    return tryLeft() ?? tryRight() ?? tryBottom();
  }
  if (preferred === "top") {
    return tryTop();
  }
  return tryBottom();
}
