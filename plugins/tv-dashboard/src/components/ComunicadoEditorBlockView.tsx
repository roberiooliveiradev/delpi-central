import {
  ComunicadoBlockView,
  ComunicadoMediaPlaceholder,
  blockCssStyle,
  comunicadoImageCropCssProperties,
  isComunicadoVisualBoxBlock,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import type { CSSProperties } from "react";

import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import { ComunicadoEditorVisualBoxBlock } from "./ComunicadoEditorVisualBoxBlock";
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
  isSelected,
}: {
  block: Extract<ComunicadoBlock, { type: "image" }>;
  style: CSSProperties;
  className?: string;
  isSelected?: boolean;
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

  const fit = block.style?.objectFit ?? "contain";

  return (
    <div className={blockClass} style={style}>
      {src ? (
        <img
          className="td-composer__media-preview"
          src={src}
          alt=""
          style={comunicadoImageCropCssProperties(block.imageCrop, fit)}
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

  if (isComunicadoVisualBoxBlock(block)) {
    return (
      <ComunicadoEditorVisualBoxBlock
        block={block}
        fontScale={fontScale}
        className={className}
        isSelected={isSelected}
        isEditingText={isEditingText}
      />
    );
  }

  if (block.type === "image") {
    return <EditorImageBlock block={block} style={style} className={className} isSelected={isSelected} />;
  }

  if (block.type === "video") {
    return (
      <div style={{ position: "relative", width: "100%", height: "100%" }}>
        <ComunicadoEditorVideoPreview block={block} style={style} className={className} />
      </div>
    );
  }

  if (block.type === "icon") {
    return (
      <div style={{ position: "relative", width: "100%", height: "100%" }}>
        <ComunicadoBlockView
          block={block}
          fontScale={fontScale}
          interactive
          embedded
          className={className}
          dataLoading={dataLoading}
        />
      </div>
    );
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
