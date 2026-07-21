import type { CSSProperties } from "react";

import { splitContentRunsIntoLines } from "./comunicadoContentList";
import {
  contentRunStyleToCss,
  hasRichTextRuns,
} from "./comunicadoContentRuns";
import { groupContentRunsForDisplay } from "./comunicadoContentList";
import {
  hasNamedStyleContentRuns,
  resolveEffectiveRunStyle,
} from "./comunicadoNamedTextStyles";
import type { ComunicadoContentRun, ComunicadoTextBlock } from "./comunicadoTypes";
import {
  resolveTextBlockDisplayRuns as resolveDynamicTextRuns,
  textBlockHasDataBinding,
} from "./textViewProjection";
import { ensureComunicadoDualClass } from "@delpi/plugin-ui/index";

type Props = {
  block: Pick<
    ComunicadoTextBlock,
    "content" | "contentRuns" | "textProjection" | "resolved" | "dataSourceId"
  >;
  as: "h1" | "p" | "span";
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
        const runStyle = resolveEffectiveRunStyle(run.style, { fontScale });
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

function RenderStyledLines({
  runs,
  baseStyle,
  fontScale = 1,
  lineClassName,
}: {
  runs: ComunicadoContentRun[];
  baseStyle?: CSSProperties;
  fontScale?: number;
  lineClassName?: string;
}) {
  const lines = splitContentRunsIntoLines(runs);
  return (
    <>
      {lines.map((line, index) => {
        const lineBaseStyle: CSSProperties = { ...baseStyle };
        if (line.namedStyle) {
          const preset = resolveEffectiveRunStyle({ namedStyle: line.namedStyle }, { fontScale });
          Object.assign(lineBaseStyle, preset);
        }
        const text = line.runs.map((run) => run.text).join("");
        if (!text && index === lines.length - 1) return null;
        return (
          <div
            key={`line-${index}-${line.namedStyle ?? "plain"}`}
            className={lineClassName}
            style={lineBaseStyle}
          >
            <RenderRuns runs={line.runs} fontScale={fontScale} />
          </div>
        );
      })}
    </>
  );
}

export function ComunicadoTextRunsView({ block, as, baseStyle, fontScale = 1, className }: Props) {
  const Tag = as;
  const runs = textBlockHasDataBinding(block)
    ? resolveDynamicTextRuns(block, block.resolved)
    : block.contentRuns && block.contentRuns.length > 0
      ? block.contentRuns
      : [{ text: block.content }];
  const segments = groupContentRunsForDisplay(runs);
  const hasLists = segments.some((segment) => segment.kind === "list");
  const hasNamedStyles = hasNamedStyleContentRuns(runs);
  const hasMultipleLines = runs.some((run) => run.text.includes("\n"));
  const showRuns = hasRichTextRuns(block) || hasLists || hasNamedStyles;
  const WrapperTag = hasLists || hasNamedStyles ? "div" : Tag;

  if (!showRuns) {
    return (
      <Tag className={className} style={baseStyle}>
        {block.content}
      </Tag>
    );
  }

  if (!hasLists && hasNamedStyles) {
    return (
      <WrapperTag
        className={ensureComunicadoDualClass(
          [className, "tdp-comunicado__rich-text"].filter(Boolean).join(" "),
        )}
        style={baseStyle}
      >
        <RenderStyledLines
          runs={runs}
          baseStyle={baseStyle}
          fontScale={fontScale}
          lineClassName={ensureComunicadoDualClass("tdp-comunicado__styled-line")}
        />
      </WrapperTag>
    );
  }

  if (!hasLists && !hasNamedStyles && hasMultipleLines) {
    return (
      <Tag
        className={ensureComunicadoDualClass(
          [className, "tdp-comunicado__rich-text"].filter(Boolean).join(" "),
        )}
        style={baseStyle}
      >
        <RenderStyledLines runs={runs} baseStyle={baseStyle} fontScale={fontScale} />
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
    <WrapperTag
      className={ensureComunicadoDualClass(
        [className, "tdp-comunicado__rich-text"].filter(Boolean).join(" "),
      )}
      style={baseStyle}
    >
      {segments.map((segment, index) => {
        if (segment.kind === "text") {
          const text = segment.runs.map((run) => run.text).join("");
          if (!text) return null;
          if (hasNamedStyleContentRuns(segment.runs)) {
            return (
              <span key={`text-${index}`} className={ensureComunicadoDualClass("tdp-comunicado__text-segment")}>
                <RenderStyledLines runs={segment.runs} baseStyle={baseStyle} fontScale={fontScale} />
              </span>
            );
          }
          return (
            <span key={`text-${index}`} className={ensureComunicadoDualClass("tdp-comunicado__text-segment")}>
              <RenderRuns runs={segment.runs} baseStyle={baseStyle} fontScale={fontScale} />
            </span>
          );
        }

        const ListTag = segment.listType === "ordered" ? "ol" : "ul";
        return (
          <ListTag
            key={`list-${index}-${segment.listType}`}
            className={ensureComunicadoDualClass(`tdp-comunicado__list tdp-comunicado__list--${segment.listType}`)}
          >
            {segment.items.map((itemRuns, itemIndex) => (
              <li key={`item-${index}-${itemIndex}`} className={ensureComunicadoDualClass("tdp-comunicado__list-item")}>
                <RenderRuns runs={itemRuns} baseStyle={baseStyle} fontScale={fontScale} />
              </li>
            ))}
          </ListTag>
        );
      })}
    </WrapperTag>
  );
}
