/**
 * TopBar collapse — canônico: hamburger + overflow (defaults do kit).
 * `rail` / `manual` estão deprecated e sem consumidores de produção.
 */
export type TopBarCollapseMode = "rail" | "hamburger";

/** `overflow` (canônico) = hamburger quando não couber; `manual` = legado. */
export type TopBarCollapseTrigger = "manual" | "overflow";

/** Preferir omitir — default do kit já é hamburger. Mantido para wiring explícito. */
export const TOP_BAR_COLLAPSE_MODE: TopBarCollapseMode = "hamburger";

/** Preferir omitir — default do kit já é overflow. Mantido para wiring explícito. */
export const TOP_BAR_COLLAPSE_TRIGGER: TopBarCollapseTrigger = "overflow";

/** Só usado se `TOP_BAR_COLLAPSE_TRIGGER === "manual"` (legado — não ativo). */
export const TOP_BAR_COLLAPSE_STORAGE_KEY = "delpi.supplies.topbar.collapsed";
