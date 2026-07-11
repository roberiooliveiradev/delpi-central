/**
 * Tamanho canônico do slide por viewportProfile da playlist.
 * A prévia lateral renderiza neste tamanho e escala uniformemente (print exato).
 */
export type ViewportPixelSize = { width: number; height: number };

const VIEWPORT_PIXEL_SIZES: Record<string, ViewportPixelSize> = {
  "720p": { width: 1280, height: 720 },
  "1080p": { width: 1920, height: 1080 },
  "4k": { width: 3840, height: 2160 },
  "1080p_portrait": { width: 1080, height: 1920 },
};

export function resolveViewportPixelSize(profile?: string | null): ViewportPixelSize {
  const key = (profile ?? "1080p").trim() || "1080p";
  return VIEWPORT_PIXEL_SIZES[key] ?? VIEWPORT_PIXEL_SIZES["1080p"];
}
