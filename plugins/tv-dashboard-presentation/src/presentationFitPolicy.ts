/**
 * Política canônica de encaixe do slide no container (modo apresentação).
 *
 * Referência de mercado:
 * - Excalibur `FitScreen` / `FitContainer` → contain (slide inteiro, letterbox OK)
 * - Excalibur `FitScreenAndZoom` → cover (só sob pedido explícito — corta bordas)
 * - Xibo / BrightSign → canvas de design + escala uniforme (nunca stretch)
 * - Adeus Pendrive / WebViews com «ajustar à tela» medem **scrollWidth/Height**.
 *   `transform: scale` NÃO reduz o layout (continua 1920×1080) → o host
 *   reescala e desloca (espaço acima + corte abaixo). Por isso o kiosk usa
 *   **`zoom`** (afeta layout) + documento com altura exata do viewport.
 *
 * Consumidores passam `surface`; o stage resolve contain|cover e o método
 * de escala. Proibido `if (mode === "public")` espalhado em views.
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
 * Como aplicar a escala uniforme no DOM.
 * - `zoom` — altera caixa de layout (scrollWidth = visual); obrigatório no kiosk
 *   para Adeus Pendrive.
 * - `transform` — só pinta; ok na prévia admin (sem host «ajustar à tela»).
 */
export type PresentationScaleMethod = "zoom" | "transform";

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
 * Kiosk → zoom (layout = visual para Adeus Pendrive).
 * Preview/thumbnail → transform (sem afetar medição do host).
 */
export function resolvePresentationScaleMethod(
  surface: PresentationFitSurface,
): PresentationScaleMethod {
  return surface === "kiosk" ? "zoom" : "transform";
}

/**
 * Resolve contain vs cover para o par design × container × surface.
 *
 * - `auto` (todas as surfaces, inclusive kiosk) → **contain** — slide inteiro;
 *   letterbox neutro se o host ≠ aspect do design.
 * - `cover` só com `fit: "cover"` explícito.
 */
export function resolvePresentationFitMode(
  input: ResolvePresentationFitModeInput,
): PresentationFitResolved {
  const fit = input.fit ?? "auto";
  if (fit === "contain" || fit === "cover") return fit;
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
