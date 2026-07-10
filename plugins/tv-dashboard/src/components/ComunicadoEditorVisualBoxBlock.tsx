import {
  isComunicadoVisualBoxBlock,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { ComunicadoEditorShapeBlock } from "./ComunicadoEditorShapeBlock";
import { ComunicadoEditorTextBlock } from "./ComunicadoEditorTextBlock";

type Props = {
  block: ComunicadoBlock;
  fontScale?: number;
  className?: string;
  isSelected: boolean;
  isEditingText: boolean;
};

/** Entrada canônica do editor para caixas visuais (heading, text, shape). */
export function ComunicadoEditorVisualBoxBlock({
  block,
  fontScale = 1,
  className = "",
  isSelected,
  isEditingText,
}: Props) {
  if (!isComunicadoVisualBoxBlock(block)) return null;

  if (block.type === "shape") {
    return (
      <ComunicadoEditorShapeBlock
        block={block}
        fontScale={fontScale}
        className={className}
        isSelected={isSelected}
        isEditing={isEditingText}
      />
    );
  }

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
