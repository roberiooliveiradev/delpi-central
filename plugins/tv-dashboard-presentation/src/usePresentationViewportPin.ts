import { useLayoutEffect, type RefObject } from "react";

/**
 * Fixa o palco kiosk no tamanho exato do viewport (Adeus Pendrive / WebView TV).
 *
 * Regras:
 * - top/left sempre 0 — `visualViewport.offset*` inflava o documento
 *   (`height + top`) e o host «ajustar à tela» deslocava o slide para baixo.
 * - html/body/#root com width/height em px iguais à área útil — scrollHeight
 *   não pode exceder a tela.
 */
export function usePresentationViewportPin(
  enabled: boolean,
  rootRef: RefObject<HTMLElement | null>,
): void {
  useLayoutEffect(() => {
    if (!enabled || typeof window === "undefined") return;

    const html = document.documentElement;
    const body = document.body;
    const appRoot = document.getElementById("root");
    if (!rootRef.current) return;

    const vv = window.visualViewport;
    const apply = () => {
      const el = rootRef.current;
      if (!el) return;
      const width = Math.max(0, Math.round(vv?.width ?? window.innerWidth));
      const height = Math.max(0, Math.round(vv?.height ?? window.innerHeight));

      el.style.position = "fixed";
      el.style.inset = "auto";
      el.style.top = "0";
      el.style.left = "0";
      el.style.width = `${width}px`;
      el.style.height = `${height}px`;
      el.style.right = "auto";
      el.style.bottom = "auto";
      el.style.overflow = "hidden";
      el.style.margin = "0";

      for (const node of [html, body, appRoot]) {
        if (!node) continue;
        node.style.overflow = "hidden";
        node.style.width = `${width}px`;
        node.style.height = `${height}px`;
        node.style.minHeight = "0";
        node.style.maxHeight = `${height}px`;
        node.style.margin = "0";
      }

      window.scrollTo(0, 0);
      html.scrollTop = 0;
      body.scrollTop = 0;
    };

    apply();
    vv?.addEventListener("resize", apply);
    vv?.addEventListener("scroll", apply);
    window.addEventListener("resize", apply);
    window.addEventListener("orientationchange", apply);

    return () => {
      vv?.removeEventListener("resize", apply);
      vv?.removeEventListener("scroll", apply);
      window.removeEventListener("resize", apply);
      window.removeEventListener("orientationchange", apply);
      const el = rootRef.current;
      if (el) {
        el.style.position = "";
        el.style.inset = "";
        el.style.top = "";
        el.style.left = "";
        el.style.width = "";
        el.style.height = "";
        el.style.right = "";
        el.style.bottom = "";
        el.style.overflow = "";
        el.style.margin = "";
      }
      for (const node of [html, body, appRoot]) {
        if (!node) continue;
        node.style.overflow = "";
        node.style.width = "";
        node.style.height = "";
        node.style.minHeight = "";
        node.style.maxHeight = "";
        node.style.margin = "";
      }
    };
  }, [enabled, rootRef]);
}
