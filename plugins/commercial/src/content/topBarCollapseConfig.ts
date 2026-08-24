/**
 * Escolha do modo visual da TopBar colapsável no Portal Comercial.
 * Altere as constantes abaixo e faça rebuild do MFE.
 */
export type TopBarCollapseMode = "rail" | "hamburger";

/** `manual` = botão + localStorage; `overflow` = hamburger quando não couber na largura. */
export type TopBarCollapseTrigger = "manual" | "overflow";

/** Troque para `"rail"` se quiser faixa compacta manual em vez de hamburger. */
export const TOP_BAR_COLLAPSE_MODE: TopBarCollapseMode = "hamburger";

/** Hamburger responsivo: colapsa só quando nav + slots não cabem na linha. */
export const TOP_BAR_COLLAPSE_TRIGGER: TopBarCollapseTrigger = "overflow";

/** Usado apenas quando `TOP_BAR_COLLAPSE_TRIGGER === "manual"`. */
export const TOP_BAR_COLLAPSE_STORAGE_KEY = "delpi.plugin-ui.topbar.collapsed";
