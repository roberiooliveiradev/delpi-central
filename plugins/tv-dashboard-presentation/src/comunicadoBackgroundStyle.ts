import type { CSSProperties } from "react";

import type { ComunicadoBackground } from "./comunicadoTypes";

/** URL persistida/enriquecida da imagem de fundo do slide. */
export function comunicadoBackgroundImageUrl(
  background: ComunicadoBackground | undefined,
): string | undefined {
  if (!background || background.type !== "image") return undefined;
  const raw = background.url ?? background.value;
  if (typeof raw !== "string") return undefined;
  const trimmed = raw.trim();
  return trimmed || undefined;
}

function cssUrl(url: string): string {
  return `url(${JSON.stringify(url)})`;
}

/**
 * Pintura CSS do fundo (cor / gradiente / fallback da imagem).
 * A imagem em tela cheia vai na camada `<img>` (`RichComunicadoBackground`)
 * com `object-fit: cover` — CSS `background-size` sozinho falhava quando a
 * moldura não tinha caixa explícita ou a URL tinha query string.
 */
export function comunicadoBackgroundCssProperties(
  background: ComunicadoBackground | undefined,
  imageUrl?: string,
): CSSProperties {
  const bg = background ?? { type: "color", value: "#ffffff" };
  const resolvedImage = imageUrl?.trim() || comunicadoBackgroundImageUrl(bg);

  if (bg.type === "image" && resolvedImage) {
    return {
      backgroundColor: "#ffffff",
      backgroundImage: cssUrl(resolvedImage),
      backgroundSize: "cover",
      backgroundPosition: "center center",
      backgroundRepeat: "no-repeat",
    };
  }

  if (bg.type === "gradient") {
    const angle = bg.angle ?? 180;
    return {
      backgroundImage: `linear-gradient(${angle}deg, ${bg.from}, ${bg.to})`,
    };
  }

  if (bg.type === "color") {
    return { backgroundColor: bg.value || "#ffffff" };
  }

  return { backgroundColor: "#ffffff" };
}

/** Cor/gradiente no root; imagem fica só na camada cover (evita crop duplo). */
export function comunicadoBackgroundRootStyle(
  background: ComunicadoBackground | undefined,
): CSSProperties {
  if (background?.type === "image") {
    return { backgroundColor: "#ffffff" };
  }
  return comunicadoBackgroundCssProperties(background);
}
