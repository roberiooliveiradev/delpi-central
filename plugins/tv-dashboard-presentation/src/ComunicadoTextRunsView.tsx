import type { CSSProperties } from "react";

import { contentRunStyleToCss, resolveTextBlockDisplayRuns } from "./comunicadoContentRuns";
import type { ComunicadoTextBlock } from "./comunicadoTypes";

type Props = {
  block: Pick<ComunicadoTextBlock, "content" | "contentRuns">;
  as: "h1" | "p";
  baseStyle?: CSSProperties;
  fontScale?: number;
  className?: string;
};

export function ComunicadoTextRunsView({ block, as, baseStyle, fontScale = 1, className }: Props) {
  const Tag = as;
  const runs = resolveTextBlockDisplayRuns(block);
  const showRuns = runs.length > 1 || runs.some((run) => run.style && Object.keys(run.style).length > 0);

  if (!showRuns) {
    return (
      <Tag className={className} style={baseStyle}>
        {block.content}
      </Tag>
    );
  }

  return (
    <Tag className={className} style={baseStyle}>
      {runs.map((run, index) => {
        const runStyle = contentRunStyleToCss(run.style, { fontScale });
        const mergedStyle =
          Object.keys(runStyle).length > 0 ? { ...baseStyle, ...runStyle } : baseStyle;
        return (
          <span key={`${index}-${run.text.slice(0, 12)}`} style={mergedStyle}>
            {run.text}
          </span>
        );
      })}
    </Tag>
  );
}
