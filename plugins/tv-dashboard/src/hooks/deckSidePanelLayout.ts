/** Layout persistente de barras laterais do deck (filmstrip / inspetor). */

export type DeckSidePanelSide = "filmstrip" | "inspector";

type PanelLimits = {
  storageWidthKey: string;
  storageCollapsedKey: string;
  defaultWidth: number;
  minWidth: number;
  maxWidth: number;
  collapsedWidth: number;
};

const PANEL_LIMITS: Record<DeckSidePanelSide, PanelLimits> = {
  filmstrip: {
    storageWidthKey: "td-deck-filmstrip-width",
    storageCollapsedKey: "td-deck-filmstrip-collapsed",
    defaultWidth: 196,
    minWidth: 140,
    maxWidth: 320,
    collapsedWidth: 40,
  },
  inspector: {
    storageWidthKey: "td-deck-inspector-width",
    storageCollapsedKey: "td-deck-inspector-collapsed",
    defaultWidth: 320,
    minWidth: 260,
    maxWidth: 560,
    collapsedWidth: 36,
  },
};

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function getDeckSidePanelLimits(side: DeckSidePanelSide): PanelLimits {
  return PANEL_LIMITS[side];
}

export function clampDeckSidePanelWidth(side: DeckSidePanelSide, width: number): number {
  const limits = PANEL_LIMITS[side];
  if (!Number.isFinite(width)) return limits.defaultWidth;
  return Math.min(limits.maxWidth, Math.max(limits.minWidth, Math.round(width)));
}

export function readDeckSidePanelWidth(side: DeckSidePanelSide): number {
  const limits = PANEL_LIMITS[side];
  if (!canUseStorage()) return limits.defaultWidth;
  try {
    const raw = window.localStorage.getItem(limits.storageWidthKey);
    if (raw == null || raw === "") return limits.defaultWidth;
    return clampDeckSidePanelWidth(side, Number(raw));
  } catch {
    return limits.defaultWidth;
  }
}

export function writeDeckSidePanelWidth(side: DeckSidePanelSide, width: number): void {
  if (!canUseStorage()) return;
  try {
    window.localStorage.setItem(
      PANEL_LIMITS[side].storageWidthKey,
      String(clampDeckSidePanelWidth(side, width)),
    );
  } catch {
    /* ignore quota / private mode */
  }
}

export function readDeckSidePanelCollapsed(side: DeckSidePanelSide): boolean {
  if (!canUseStorage()) return false;
  try {
    return window.localStorage.getItem(PANEL_LIMITS[side].storageCollapsedKey) === "1";
  } catch {
    return false;
  }
}

export function writeDeckSidePanelCollapsed(side: DeckSidePanelSide, collapsed: boolean): void {
  if (!canUseStorage()) return;
  try {
    window.localStorage.setItem(PANEL_LIMITS[side].storageCollapsedKey, collapsed ? "1" : "0");
  } catch {
    /* ignore */
  }
}
