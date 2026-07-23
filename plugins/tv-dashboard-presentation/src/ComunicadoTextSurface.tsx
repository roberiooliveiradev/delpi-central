import type { CSSProperties, ReactNode } from "react";

import { ComunicadoTextRunsView } from "./ComunicadoTextRunsView";
import { hasRichTextRuns } from "./comunicadoContentRuns";
import { hasListContentRuns } from "./comunicadoContentList";
import { hasNamedStyleContentRuns } from "./comunicadoNamedTextStyles";
import type { ComunicadoContentRun } from "./comunicadoTypes";
import {
  resolveVisualBoxProfile,
  type ComunicadoVisualBoxBlock,
} from "./comunicadoVisualBox";
import { resolveVisualBoxDisplayText } from "./textViewProjection";

export type TextSurfaceDisplay = {
  content: string;
  contentRuns?: ComunicadoContentRun[];
};

/** Resolve texto de exibição (com ou sem data binding) — caminho único. */
export function resolveTextSurfaceDisplay(
  block: ComunicadoVisualBoxBlock,
): TextSurfaceDisplay {
  const resolved = "resolved" in block ? block.resolved : undefined;
  const display = resolveVisualBoxDisplayText(block, resolved);
  return {
    content: display.content ?? "",
    contentRuns: display.contentRuns,
  };
}

/** Há formatação de caractere, lista ou estilo nomeado a pintar via TextRunsView. */
export function textSurfaceNeedsRichPaint(display: TextSurfaceDisplay): boolean {
  if (hasRichTextRuns(display)) return true;
  const runs = display.contentRuns;
  if (!runs?.length) return false;
  return hasListContentRuns(runs) || hasNamedStyleContentRuns(runs);
}

/**
 * Superfície canônica de texto da caixa visual (heading / text / shape).
 * Sempre resolve display e pinta via `ComunicadoTextRunsView` quando há runs ricos.
 */
export function ComunicadoTextSurface({
  block,
  fontScale = 1,
  className,
  baseStyle,
  as,
  emptyFallback = null,
}: {
  block: ComunicadoVisualBoxBlock;
  fontScale?: number;
  className?: string;
  baseStyle?: CSSProperties;
  /** Override da tag; default vem do perfil da caixa. */
  as?: "h1" | "p" | "span";
  emptyFallback?: ReactNode;
}) {
  const profile = resolveVisualBoxProfile(block);
  const display = resolveTextSurfaceDisplay(block);
  const Tag = as ?? profile.textTag;
  const hasText = Boolean(display.content.trim()) || Boolean(display.contentRuns?.length);

  if (!hasText) return <>{emptyFallback}</>;

  return (
    <ComunicadoTextRunsView
      block={{
        content: display.content,
        contentRuns: display.contentRuns,
        textProjection: block.textProjection,
        resolved: "resolved" in block ? block.resolved : undefined,
        dataSourceId: block.dataSourceId,
      }}
      as={Tag}
      baseStyle={baseStyle}
      fontScale={fontScale}
      className={className}
    />
  );
}
