/**
 * Escolha do modo visual da TopBar colapsável no Portal Comercial.
 * Altere só `TOP_BAR_COLLAPSE_MODE` e faça rebuild do MFE.
 */
export type TopBarCollapseMode = "rail" | "hamburger";

/** Troque esta constante para `"hamburger"` ou `"rail"`. */
export const TOP_BAR_COLLAPSE_MODE: TopBarCollapseMode = "rail";

export const TOP_BAR_COLLAPSE_STORAGE_KEY = "delpi.plugin-ui.topbar.collapsed";
