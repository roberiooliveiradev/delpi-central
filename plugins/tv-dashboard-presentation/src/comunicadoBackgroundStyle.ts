import type { CSSProperties } from "react";

import type { ComunicadoBackground } from "./comunicadoTypes";

export function comunicadoBackgroundCssProperties(
  background: ComunicadoBackground | undefined,
  imageUrl?: string,
): CSSProperties {
  const bg = background ?? { type: "color", value: "#0f172a" };

  if (bg.type === "image" && imageUrl) {
    return {
      backgroundImage: `url(${imageUrl})`,
      backgroundSize: "cover",
      backgroundPosition: "center",
    };
  }

  if (bg.type === "gradient") {
    const angle = bg.angle ?? 180;
    return {
      backgroundImage: `linear-gradient(${angle}deg, ${bg.from}, ${bg.to})`,
    };
  }

  if (bg.type === "color") {
    return { backgroundColor: bg.value || "#0f172a" };
  }

  return { backgroundColor: "#0f172a" };
}
