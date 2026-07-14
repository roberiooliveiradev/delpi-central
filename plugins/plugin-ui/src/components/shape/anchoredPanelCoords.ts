export type AnchoredPanelPlacement = "bottom" | "top" | "right" | "left";

export type AnchoredPanelCoordsInput = {
  anchor: { left: number; top: number; right: number; bottom: number; width: number; height: number };
  panelWidth: number;
  panelHeight: number;
  gap?: number;
  margin?: number;
  viewportWidth: number;
  viewportHeight: number;
  /** Preferência: usa se couber; senão tenta alternativas e cai para baixo/cima. */
  preferredPlacement?: AnchoredPanelPlacement;
  /**
   * Quando false, `bottom`/`top` não invertem o lado — só clamp no viewport.
   * Útil na ribbon do editor (evita painel subir e cobrir a faixa).
   */
  allowFlip?: boolean;
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

function spaceBelow(anchor: AnchoredPanelCoordsInput["anchor"], gap: number, vh: number): number {
  return vh - anchor.bottom - gap;
}

function spaceAbove(anchor: AnchoredPanelCoordsInput["anchor"], gap: number): number {
  return anchor.top - gap;
}

/**
 * Posiciona painel ancorado. Com `preferredPlacement: "right"|"left"`, fica ao lado
 * do gatilho quando há espaço; senão usa baixo/cima.
 */
export function resolveAnchoredPanelCoords(input: AnchoredPanelCoordsInput): AnchoredPanelCoords {
  const gap = input.gap ?? 4;
  const margin = input.margin ?? 8;
  const allowFlip = input.allowFlip !== false;
  const { anchor, panelWidth, panelHeight, viewportWidth: vw, viewportHeight: vh } = input;
  const preferred = input.preferredPlacement ?? "bottom";

  const alignVerticalBeside = (): number => {
    if (panelHeight <= 0) return anchor.top;
    return clamp(anchor.top, margin, Math.max(margin, vh - panelHeight - margin));
  };

  const alignHorizontalBelow = (): number => {
    if (panelWidth <= 0) return anchor.left;
    return clamp(anchor.left, margin, Math.max(margin, vw - panelWidth - margin));
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
    if (panelHeight > 0 && top + panelHeight > vh - margin) {
      if (allowFlip) {
        const above = anchor.top - panelHeight - gap;
        top = above >= margin ? above : Math.max(margin, vh - panelHeight - margin);
        return { placement: above >= margin ? "top" : "bottom", left: alignHorizontalBelow(), top };
      }
      top = Math.max(margin, vh - panelHeight - margin);
    }
    return { placement: "bottom", left: alignHorizontalBelow(), top };
  };

  const tryTop = (): AnchoredPanelCoords => {
    let top = anchor.top - panelHeight - gap;
    if (panelHeight > 0 && top < margin) {
      if (allowFlip) {
        const below = anchor.bottom + gap;
        if (below + panelHeight <= vh - margin || spaceBelow(anchor, gap, vh) >= spaceAbove(anchor, gap)) {
          return { placement: "bottom", left: alignHorizontalBelow(), top: below };
        }
      }
      top = margin;
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
