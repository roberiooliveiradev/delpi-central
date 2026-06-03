export const MDC_MODAL_ROOT_ID = "mdc-modal-root";

/** Área de overlay/menus limitada ao MFE (não cobre sidebar do portal). */
export function resolveModalPortalContainer(): HTMLElement {
  if (typeof document === "undefined") {
    throw new Error("resolveModalPortalContainer requires a DOM");
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
