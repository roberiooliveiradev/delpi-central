/**
 * TopBar collapse — canônico: hamburger + overflow (defaults do kit).
 * `rail` / `manual` estão deprecated e sem consumidores de produção.
 */
export type TopBarCollapseMode = "rail" | "hamburger";
export type TopBarCollapseTrigger = "manual" | "overflow";

export const TOP_BAR_COLLAPSE_MODE: TopBarCollapseMode = "hamburger";
export const TOP_BAR_COLLAPSE_TRIGGER: TopBarCollapseTrigger = "overflow";
/** Só usado se trigger === "manual" (legado — não ativo). */
export const TOP_BAR_COLLAPSE_STORAGE_KEY = "delpi.maintenance.topbar.collapsed";
