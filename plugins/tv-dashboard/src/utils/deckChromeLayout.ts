/**
 * Preferência de top bar recolhida — removida (jul/2026).
 * A barra não minimiza mais; sem seleção o chrome volta para a aba Inserir.
 * Mantido só para limpar localStorage legado.
 */

const STORAGE_COLLAPSED_KEY = "td-deck-chrome-collapsed";

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

/** Remove flag legado de chrome recolhido (no-op se já limpo). */
export function clearLegacyDeckChromeCollapsed(): void {
  if (!canUseStorage()) return;
  try {
    window.localStorage.removeItem(STORAGE_COLLAPSED_KEY);
  } catch {
    /* ignore */
  }
}
