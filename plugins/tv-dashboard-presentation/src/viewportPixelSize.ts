/**
 * Tamanho canônico do slide por `viewportProfile` da playlist.
 * Tipografia e chrome em px de design; encaixe visual via escala uniforme (não stretch).
 *
 * Custom: `viewportProfile === "custom"` + width/height em px (playlist).
 */
import { clampDesignPx } from "./viewportLengthUnits";

export type ViewportPixelSize = { width: number; height: number };

export type ViewportProfileOption = {
  value: string;
  /** Rótulo curto para selects (PT). */
  label: string;
  width: number;
  height: number;
};

const VIEWPORT_PIXEL_SIZES: Record<string, ViewportPixelSize> = {
  "720p": { width: 1280, height: 720 },
  "1080p": { width: 1920, height: 1080 },
  "1366x768": { width: 1366, height: 768 },
  "1920x1200": { width: 1920, height: 1200 },
  "2560x1440": { width: 2560, height: 1440 },
  "4k": { width: 3840, height: 2160 },
  "3840x1080": { width: 3840, height: 1080 },
  "1080p_portrait": { width: 1080, height: 1920 },
  "768x1366": { width: 768, height: 1366 },
};

/** Perfis nomeados (sem Personalizado). Ordem de exibição na UI. */
export const VIEWPORT_PROFILE_PRESETS: readonly ViewportProfileOption[] = [
  { value: "1080p", label: "1920×1080 (Full HD)", ...VIEWPORT_PIXEL_SIZES["1080p"] },
  { value: "1080p_portrait", label: "1080×1920 (Retrato)", ...VIEWPORT_PIXEL_SIZES["1080p_portrait"] },
  { value: "720p", label: "1280×720 (HD)", ...VIEWPORT_PIXEL_SIZES["720p"] },
  { value: "1366x768", label: "1366×768", ...VIEWPORT_PIXEL_SIZES["1366x768"] },
  { value: "1920x1200", label: "1920×1200", ...VIEWPORT_PIXEL_SIZES["1920x1200"] },
  { value: "2560x1440", label: "2560×1440 (QHD)", ...VIEWPORT_PIXEL_SIZES["2560x1440"] },
  { value: "4k", label: "3840×2160 (4K)", ...VIEWPORT_PIXEL_SIZES["4k"] },
  { value: "3840x1080", label: "3840×1080 (Ultrawide)", ...VIEWPORT_PIXEL_SIZES["3840x1080"] },
  { value: "768x1366", label: "768×1366 (Retrato)", ...VIEWPORT_PIXEL_SIZES["768x1366"] },
];

export const VIEWPORT_CUSTOM_PROFILE = "custom";

export type ResolveViewportPixelSizeOptions = {
  width?: number | null;
  height?: number | null;
};

export function isNamedViewportProfile(profile?: string | null): boolean {
  const key = (profile ?? "").trim();
  return Boolean(key && key !== VIEWPORT_CUSTOM_PROFILE && VIEWPORT_PIXEL_SIZES[key]);
}

export function isCustomViewportProfile(profile?: string | null): boolean {
  return (profile ?? "").trim() === VIEWPORT_CUSTOM_PROFILE;
}

/**
 * Resolve px de design. Custom exige width/height válidos; senão cai em 1080p.
 */
export function resolveViewportPixelSize(
  profile?: string | null,
  dims?: ResolveViewportPixelSizeOptions | null,
): ViewportPixelSize {
  const key = (profile ?? "1080p").trim() || "1080p";
  if (key === VIEWPORT_CUSTOM_PROFILE) {
    const width = Number(dims?.width);
    const height = Number(dims?.height);
    if (Number.isFinite(width) && Number.isFinite(height) && width > 0 && height > 0) {
      return { width: clampDesignPx(width), height: clampDesignPx(height) };
    }
    return VIEWPORT_PIXEL_SIZES["1080p"];
  }
  return VIEWPORT_PIXEL_SIZES[key] ?? VIEWPORT_PIXEL_SIZES["1080p"];
}

/** Opções do select incluindo Personalizado (sem width/height fixos). */
export function listViewportProfileSelectOptions(): Array<{ value: string; label: string }> {
  return [
    ...VIEWPORT_PROFILE_PRESETS.map((item) => ({ value: item.value, label: item.label })),
    { value: VIEWPORT_CUSTOM_PROFILE, label: "Personalizado…" },
  ];
}
