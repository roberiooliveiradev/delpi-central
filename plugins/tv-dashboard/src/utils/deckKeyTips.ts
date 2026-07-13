import type { DeckRibbonTabId } from "../components/deck/deckRibbonTabMeta";
import { DECK_RIBBON_TABS } from "../components/deck/deckRibbonTabMeta";

export type DeckKeyTipScope = "tabs" | "actions";
export type DeckKeyTipMode = "idle" | "tabs" | "actions";

/**
 * Teclas de função das abas (escopo `tabs`), na ordem canônica de `DECK_RIBBON_TABS`.
 * F1 = Página Inicial, F2 = Inserir, …
 */
export const DECK_TAB_KEYTIPS: Record<DeckRibbonTabId, string> = Object.fromEntries(
  DECK_RIBBON_TABS.map((tab, index) => [tab.id, `F${index + 1}`]),
) as Record<DeckRibbonTabId, string>;

/** Ações da Página Inicial (Escopo `actions`). */
export const DECK_HOME_ACTION_KEYTIPS = {
  newSlide: "N",
  prevSlide: "A",
  nextSlide: "S",
  toggleActive: "U",
  duplicate: "D",
  exportPng: "1",
  exportPdf: "2",
  exportPptx: "3",
  remove: "E",
} as const;

/** Ações da aba Exibir. */
export const DECK_VIEW_ACTION_KEYTIPS = {
  zoomOut: "O",
  zoomIn: "M",
  zoomFit: "J",
  zoom100: "Z",
  rulers: "R",
  grid: "Q",
  guides: "Y",
  snap: "W",
  shortcuts: "K",
} as const;

/** Ações principais da aba Inserir. */
export const DECK_INSERT_ACTION_KEYTIPS = {
  heading: "H",
  text: "X",
  image: "M",
  video: "W",
  shape: "O",
  icon: "C",
  canvasTable: "A",
  dataSource: "S",
  kpi: "K",
  chart: "G",
  table: "B",
} as const;

const FUNCTION_KEY_RE = /^F([1-9]|1[0-2])$/i;

export function isDeckFunctionKeyName(raw: string): boolean {
  return FUNCTION_KEY_RE.test(raw.trim());
}

export function normalizeKeyTipLetter(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "";
  if (isDeckFunctionKeyName(trimmed)) return trimmed.toUpperCase();
  if (trimmed === " ") return "SPACE";
  return trimmed.length === 1 ? trimmed.toUpperCase() : trimmed.toUpperCase();
}

/** Tecla F1–F12 (sem modificadores) para KeyTips de aba. */
export function isDeckKeyTipFunctionKey(event: KeyboardEvent): boolean {
  if (event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return false;
  return isDeckFunctionKeyName(event.key);
}

/** Tecla de ação válida para KeyTips da ribbon (letra, dígito). */
export function isDeckKeyTipActionKey(event: KeyboardEvent): boolean {
  if (event.ctrlKey || event.metaKey || event.altKey) return false;
  if (event.key.length !== 1) return false;
  return /^[a-zA-Z0-9]$/.test(event.key);
}

/**
 * Dispara o controle anotado com `data-td-keytip` no escopo informado.
 * Retorna true se encontrou alvo visível e clicável.
 */
export function activateDeckKeyTipTarget(scope: DeckKeyTipScope, letter: string): boolean {
  const tip = normalizeKeyTipLetter(letter);
  const hosts = Array.from(
    document.querySelectorAll<HTMLElement>(
      `[data-td-keytip-scope="${scope}"][data-td-keytip="${tip}"]`,
    ),
  ).filter((el) => {
    if (el.closest("[aria-hidden='true']")) return false;
    const style = window.getComputedStyle(el);
    return style.display !== "none" && style.visibility !== "hidden";
  });

  const host = hosts[0];
  if (!host) return false;

  const control = host.querySelector<HTMLElement>(
    [
      "button:not([disabled])",
      "[role='tab']:not([aria-disabled='true'])",
      "[role='button']:not([aria-disabled='true'])",
    ].join(","),
  );

  const target = control ?? host;
  if (target instanceof HTMLButtonElement && target.disabled) return false;
  if (target.getAttribute("aria-disabled") === "true") return false;
  if (target.getAttribute("disabled") != null) return false;

  target.click();
  return true;
}
