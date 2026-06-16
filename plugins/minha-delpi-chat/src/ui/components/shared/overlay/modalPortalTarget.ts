export const MDC_MODAL_ROOT_ID = "mdc-modal-root";

/** Portal de overlay limitado ao MFE (não cobre a sidebar do host). */
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

/** @deprecated Use resolveOverlayPortalContainer */
export function resolveModalPortalContainer(): HTMLElement {
  return resolveOverlayPortalContainer();
}
