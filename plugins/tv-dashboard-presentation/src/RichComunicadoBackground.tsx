import type { CSSProperties } from "react";
import { comunicadoStageBemClasses, ensureComunicadoDualClass } from "@delpi/plugin-ui/index";

export type RichComunicadoBackgroundProps = {
  url?: string | null;
  className?: string;
};

const DEFAULT_BEM = comunicadoStageBemClasses("tdp");

/** Inline: cobre a moldura mesmo se o CSS do kit atrasar no Module Federation. */
const COVER_STYLE: CSSProperties = {
  position: "absolute",
  inset: 0,
  display: "block",
  width: "100%",
  height: "100%",
  maxWidth: "none",
  maxHeight: "none",
  margin: 0,
  padding: 0,
  border: 0,
  objectFit: "cover",
  objectPosition: "center",
  pointerEvents: "none",
  userSelect: "none",
  zIndex: 0,
};

/**
 * Imagem de fundo canônica — preenche a moldura 16:9 (cover, centro).
 * Editor e TV usam o mesmo componente; não reimplementar no composer.
 */
export function RichComunicadoBackground({ url, className }: RichComunicadoBackgroundProps) {
  if (!url) return null;
  return (
    <img
      className={ensureComunicadoDualClass(className ?? DEFAULT_BEM.background)}
      src={url}
      alt=""
      draggable={false}
      aria-hidden
      style={COVER_STYLE}
    />
  );
}
