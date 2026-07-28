/**
 * Política canônica de encaixe do slide no container (modo apresentação).
 *
 * Referência de mercado:
 * - Excalibur `FitScreen` / `FitContainer` → contain (slide inteiro, letterbox OK)
 * - Excalibur `FitScreenAndZoom` → cover (só sob pedido explícito — corta bordas)
 * - Xibo / BrightSign → canvas de design + `transform: scale` uniforme (nunca stretch)
 * - Players com «ajustar à tela» (ex.: Adeus Pendrive) → o HTML deve usar **contain**;
 *   cover + scale do host = zoom duplo e corte em baixo/lados
 *
 * Consumidores passam `surface`; o stage resolve contain|cover. Proibido
 * `if (mode === "public")` espalhado em views.
 */

export type PresentationFitSurface = "kiosk" | "preview" | "thumbnail";

/** Resultado efetivo aplicado no scale (nunca stretch). */
export type PresentationFitResolved = "contain" | "cover";

/**
 * Pedido explícito ou `auto` (resolve por surface).
 * Default do stage: `auto` → contain em todas as surfaces.
 */
export type PresentationFitMode = PresentationFitResolved | "auto";

/**
 * Quão perto os aspects precisam estar para tratar como «mesma família»
 * (reservado; auto kiosk usa contain por causa de hosts com scale próprio).
 */
export const PRESENTATION_FIT_ASPECT_NEAR_RATIO = 1.12;

export type ResolvePresentationFitModeInput = {
  surface: PresentationFitSurface;
  designWidth: number;
  designHeight: number;
  containerWidth?: number;
  containerHeight?: number;
  /** Força contain|cover; `auto` → contain (seguro com Adeus Pendrive / WebView). */
  fit?: PresentationFitMode;
};

/** Mapeia o modo da view (public/preview) para a surface da política — único ponto. */
export function presentationSurfaceFromViewMode(
  mode: "public" | "preview",
): PresentationFitSurface {
  return mode === "public" ? "kiosk" : "preview";
}

/**
 * Resolve contain vs cover para o par design × container × surface.
 *
 * - `auto` (todas as surfaces, inclusive kiosk) → **contain** — slide inteiro;
 *   letterbox neutro se o host ≠ aspect do design. Evita corte com apps que
 *   já fazem «ajustar à tela» (Adeus Pendrive).
 * - `cover` só com `fit: "cover"` explícito (wall sem scale do host).
 */
export function resolvePresentationFitMode(
  input: ResolvePresentationFitModeInput,
): PresentationFitResolved {
  const fit = input.fit ?? "auto";
  if (fit === "contain" || fit === "cover") return fit;
  // auto: contain em todas as surfaces (kiosk incluído — Adeus Pendrive etc.)
  return "contain";
}

/**
 * Mede a área útil para escala: bbox do nó ∩ visualViewport (quando existe).
 * Evita letterbox/shift quando o host reporta client* maior que a área visível.
 */
export function measurePresentationViewportSize(node: HTMLElement): {
  width: number;
  height: number;
} {
  const rect = node.getBoundingClientRect();
  let width = rect.width > 0 ? rect.width : node.clientWidth;
  let height = rect.height > 0 ? rect.height : node.clientHeight;

  const vv = typeof window !== "undefined" ? window.visualViewport : null;
  if (vv && vv.width > 0 && vv.height > 0) {
    width = Math.min(width, vv.width);
    height = Math.min(height, vv.height);
  }

  return {
    width: Math.max(0, width),
    height: Math.max(0, height),
  };
}
