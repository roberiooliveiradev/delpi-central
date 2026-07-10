import type { CSSProperties } from "react";

import {
  contentRunStyleToCss,
  hasRichTextRuns,
  resolveTextBlockDisplayRuns,
} from "./comunicadoContentRuns";
import { groupContentRunsForDisplay } from "./comunicadoContentList";
import type { ComunicadoContentRun, ComunicadoTextBlock } from "./comunicadoTypes";

type Props = {
  block: Pick<ComunicadoTextBlock, "content" | "contentRuns">;
  as: "h1" | "p";
  baseStyle?: CSSProperties;
  fontScale?: number;
  className?: string;
};

function RenderRuns({
  runs,
  baseStyle,
  fontScale = 1,
}: {
  runs: ComunicadoContentRun[];
  baseStyle?: CSSProperties;
  fontScale?: number;
}) {
  const showRuns = runs.length > 1 || runs.some((run) => run.style && Object.keys(run.style).length > 0);
  if (!showRuns) {
    return <>{runs.map((run) => run.text).join("")}</>;
  }

  return (
    <>
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
    </>
  );
}

export function ComunicadoTextRunsView({ block, as, baseStyle, fontScale = 1, className }: Props) {
  const Tag = as;
  const runs = resolveTextBlockDisplayRuns(block);
  const segments = groupContentRunsForDisplay(runs);
  const hasLists = segments.some((segment) => segment.kind === "list");
  const showRuns = hasRichTextRuns(block) || hasLists;
  const WrapperTag = hasLists ? "div" : Tag;

  if (!showRuns) {
    return (
      <Tag className={className} style={baseStyle}>
        {block.content}
      </Tag>
    );
  }

  if (!hasLists) {
    return (
      <Tag className={className} style={baseStyle}>
        <RenderRuns runs={runs} baseStyle={baseStyle} fontScale={fontScale} />
      </Tag>
    );
  }

  return (
    <WrapperTag className={[className, "tdp-comunicado__rich-text"].filter(Boolean).join(" ")} style={baseStyle}>
      {segments.map((segment, index) => {
        if (segment.kind === "text") {
          const text = segment.runs.map((run) => run.text).join("");
          if (!text) return null;
          return (
            <span key={`text-${index}`} className="tdp-comunicado__text-segment">
              <RenderRuns runs={segment.runs} baseStyle={baseStyle} fontScale={fontScale} />
            </span>
          );
        }

        const ListTag = segment.listType === "ordered" ? "ol" : "ul";
        return (
          <ListTag
            key={`list-${index}-${segment.listType}`}
            className={`tdp-comunicado__list tdp-comunicado__list--${segment.listType}`}
          >
            {segment.items.map((itemRuns, itemIndex) => (
              <li key={`item-${index}-${itemIndex}`} className="tdp-comunicado__list-item">
                <RenderRuns runs={itemRuns} baseStyle={baseStyle} fontScale={fontScale} />
              </li>
            ))}
          </ListTag>
        );
      })}
    </WrapperTag>
  );
}
