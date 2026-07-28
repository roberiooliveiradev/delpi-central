/**
 * Política canônica de encaixe do slide no container (modo apresentação).
 *
 * Referência de mercado:
 * - Excalibur `FitScreen` / `FitContainer` → contain (slide inteiro, letterbox OK)
 * - Excalibur `FitScreenAndZoom` → cover (preenche, corta bordas; wall/signage)
 * - Xibo / BrightSign → canvas de design + `transform: scale` uniforme (nunca stretch)
 * - Android TV → margem ~5% overscan no conteúdo; fundo pode sangrar
 *
 * Consumidores passam `surface`; o stage resolve contain|cover. Proibido
 * `if (mode === "public")` espalhado em views.
 */

export type PresentationFitSurface = "kiosk" | "preview" | "thumbnail";

/** Resultado efetivo aplicado no scale (nunca stretch). */
export type PresentationFitResolved = "contain" | "cover";

/**
 * Pedido explícito ou `auto` (resolve por surface + orientação do container).
 * Default do stage: `auto`.
 */
export type PresentationFitMode = PresentationFitResolved | "auto";

/**
 * Quão perto os aspects precisam estar para tratar como «mesma família»
 * (só documentado; kiosk same-orientation já usa cover).
 */
export const PRESENTATION_FIT_ASPECT_NEAR_RATIO = 1.12;

export type ResolvePresentationFitModeInput = {
  surface: PresentationFitSurface;
  designWidth: number;
  designHeight: number;
  /** Se omitido no kiosk, assume cover (wall). */
  containerWidth?: number;
  containerHeight?: number;
  /** Força contain|cover; `auto` delega à regra de surface. */
  fit?: PresentationFitMode;
};

/** Mapeia o modo da view (public/preview) para a surface da política — único ponto. */
export function presentationSurfaceFromViewMode(
  mode: "public" | "preview",
): PresentationFitSurface {
  return mode === "public" ? "kiosk" : "preview";
}

function isLandscape(width: number, height: number): boolean {
  return width >= height;
}

/**
 * Resolve contain vs cover para o par design × container × surface.
 *
 * - preview / thumbnail → sempre contain (ver slide inteiro).
 * - kiosk → cover se mesma orientação (FitScreenAndZoom); contain se
 *   orientação diverge (ex.: playlist portrait em TV landscape).
 */
export function resolvePresentationFitMode(
  input: ResolvePresentationFitModeInput,
): PresentationFitResolved {
  const fit = input.fit ?? "auto";
  if (fit === "contain" || fit === "cover") return fit;

  if (input.surface === "preview" || input.surface === "thumbnail") {
    return "contain";
  }

  // kiosk
  const { designWidth, designHeight, containerWidth, containerHeight } = input;
  if (
    !(designWidth > 0) ||
    !(designHeight > 0) ||
    containerWidth == null ||
    containerHeight == null ||
    !(containerWidth > 0) ||
    !(containerHeight > 0)
  ) {
    return "cover";
  }

  const designLandscape = isLandscape(designWidth, designHeight);
  const containerLandscape = isLandscape(containerWidth, containerHeight);
  if (designLandscape !== containerLandscape) {
    return "contain";
  }
  return "cover";
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
