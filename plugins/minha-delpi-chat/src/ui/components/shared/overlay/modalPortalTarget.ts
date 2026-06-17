export const MDC_MODAL_ROOT_ID = "mdc-modal-root";
export const MDC_SIDEBAR_SELECTOR = ".mdc-chat-sidebar";

/**
 * Camada única de overlay do MFE — modais, popovers e menus ancorados.
 * `#mdc-modal-root` fica em `.minha-delpi-chat` (acima do drawer mobile).
 */
export function resolveOverlayPortalContainer(): HTMLElement {
  if (typeof document === "undefined") {
    throw new Error("resolveOverlayPortalContainer requires a DOM");
  }

  const root = document.getElementById(MDC_MODAL_ROOT_ID);

  if (root instanceof HTMLElement) {
    return root;
  }

  const app = document.querySelector<HTMLElement>(".minha-delpi-chat");

  if (app) {
    return app;
  }

  return document.body;
}

export function isOverlayPortalContained(container: HTMLElement): boolean {
  return container !== document.body;
}

export type AnchoredMenuPortalTarget = {
  container: HTMLElement;
  contained: boolean;
};

export function findSidebarMenuPortalContainer(
  trigger?: HTMLElement | null,
): HTMLElement | null {
  if (!trigger) {
    return null;
  }

  return trigger.closest<HTMLElement>(MDC_SIDEBAR_SELECTOR);
}

/** Portal canônico — menus da sidebar vão para `.minha-delpi-chat` (acima do drawer). */
export function resolveAnchoredMenuPortalTarget(
  trigger?: HTMLElement | null,
): AnchoredMenuPortalTarget {
  const sidebar = findSidebarMenuPortalContainer(trigger);

  if (sidebar) {
    const shell =
      sidebar.closest<HTMLElement>(".minha-delpi-chat") ??
      resolveOverlayPortalContainer();

    return { container: shell, contained: false };
  }

  const container = resolveOverlayPortalContainer();

  return {
    container,
    contained: isOverlayPortalContained(container),
  };
}

export function isSidebarMenuTrigger(
  trigger: HTMLElement | null | undefined,
): boolean {
  return Boolean(trigger?.closest(MDC_SIDEBAR_SELECTOR));
}

/** @deprecated Use resolveAnchoredMenuPortalTarget */
export function resolveAnchoredMenuPortalContainer(_options?: {
  useViewportPositioning?: boolean;
}): HTMLElement {
  return resolveAnchoredMenuPortalTarget().container;
}

/** @deprecated Use resolveOverlayPortalContainer */
export function resolveModalPortalContainer(): HTMLElement {
  return resolveOverlayPortalContainer();
}
