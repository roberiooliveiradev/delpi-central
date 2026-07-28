import { useLayoutEffect, type RefObject } from "react";

/**
 * Fixa o palco kiosk no visualViewport (padrão de signage / WebView TV).
 *
 * Apps que roteiam o link (ex.: «ajustar à tela») e browsers com chrome
 * deslocam o layout viewport vs. a área visível (`offsetTop`/`offsetLeft`).
 * Sem este pin, o slide parece letterbox assimétrico e «cai» para baixo.
 *
 * Sem `visualViewport` (WebViews antigos): usa `innerWidth`/`innerHeight`.
 */
export function useKioskVisualViewportPin(
  enabled: boolean,
  rootRef: RefObject<HTMLElement | null>,
): void {
  useLayoutEffect(() => {
    if (!enabled || typeof window === "undefined") return;

    const root = rootRef.current;
    const html = document.documentElement;
    const body = document.body;
    if (!root) return;

    const vv = window.visualViewport;
    const apply = () => {
      const el = rootRef.current;
      if (!el) return;
      const width = vv?.width ?? window.innerWidth;
      const height = vv?.height ?? window.innerHeight;
      const top = vv?.offsetTop ?? 0;
      const left = vv?.offsetLeft ?? 0;

      el.style.position = "fixed";
      el.style.inset = "auto";
      el.style.top = `${top}px`;
      el.style.left = `${left}px`;
      el.style.width = `${Math.max(0, width)}px`;
      el.style.height = `${Math.max(0, height)}px`;
      el.style.right = "auto";
      el.style.bottom = "auto";
      el.style.overflow = "hidden";

      html.style.overflow = "hidden";
      body.style.overflow = "hidden";
      html.style.height = `${Math.max(0, height + top)}px`;
      body.style.height = `${Math.max(0, height + top)}px`;
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
      }
      html.style.overflow = "";
      body.style.overflow = "";
      html.style.height = "";
      body.style.height = "";
    };
  }, [enabled, rootRef]);
}
