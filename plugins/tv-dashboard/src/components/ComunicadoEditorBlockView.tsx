import { ComunicadoBlockView, ComunicadoMediaPlaceholder, blockCssStyle, type ComunicadoBlock } from "@delpi/tv-dashboard-presentation";
import type { CSSProperties } from "react";

import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import { ComunicadoEditorTextBlock } from "./ComunicadoEditorTextBlock";
import { ComunicadoEditorVideoPreview } from "./ComunicadoEditorVideoPreview";

type Props = {
  block: ComunicadoBlock;
  fontScale?: number;
  className?: string;
  isSelected?: boolean;
  isEditingText?: boolean;
  dataLoading?: boolean;
};

function EditorImageBlock({
  block,
  style,
  className,
}: {
  block: Extract<ComunicadoBlock, { type: "image" }>;
  style: CSSProperties;
  className?: string;
}) {
  const { src, loading, error } = useAuthenticatedBlobUrl(block.url);

  const blockClass = [
    "tdp-comunicado__block",
    "tdp-comunicado__block--image",
    "tdp-comunicado__block--media",
    "td-composer__media-block",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={blockClass} style={style}>
      {src ? (
        <img
          className="td-composer__media-preview"
          src={src}
          alt=""
          style={{ objectFit: block.style?.objectFit ?? "contain" }}
        />
      ) : block.url && loading ? (
        <ComunicadoMediaPlaceholder kind="image" state="loading" />
      ) : block.url && error ? (
        <ComunicadoMediaPlaceholder kind="image" state="error" />
      ) : (
        <ComunicadoMediaPlaceholder kind="image" />
      )}
    </div>
  );
}

/** Renderização de blocos no editor — mídia autenticada e controles de vídeo. */
export function ComunicadoEditorBlockView({
  block,
  fontScale = 1,
  className = "",
  isSelected = false,
  isEditingText = false,
  dataLoading = false,
}: Props) {
  const style: CSSProperties = {
    ...blockCssStyle(block, { fontScale }),
    position: "relative",
    left: undefined,
    top: undefined,
    width: "100%",
    height: "100%",
  };

  if (block.type === "heading" || block.type === "text") {
    return (
      <ComunicadoEditorTextBlock
        block={block}
        fontScale={fontScale}
        className={className}
        isSelected={isSelected}
        isEditing={isEditingText}
      />
    );
  }

  if (block.type === "image") {
    return <EditorImageBlock block={block} style={style} className={className} />;
  }

  if (block.type === "video") {
    return <ComunicadoEditorVideoPreview block={block} style={style} className={className} />;
  }

  return (
    <ComunicadoBlockView
      block={block}
      fontScale={fontScale}
      interactive
      embedded
      className={className}
      dataLoading={dataLoading}
    />
  );
}
