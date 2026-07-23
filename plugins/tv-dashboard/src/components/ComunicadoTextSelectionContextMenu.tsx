import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  ContextMenuToolbar,
  ContextMenuToolbarButton,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import { Bold, Italic, RemoveFormatting, Strikethrough, Underline } from "lucide-react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { PRESERVE_TEXT_EDIT_FOCUS_ATTR } from "../utils/preserveTextEditFocus";
import { useComunicadoEditor } from "./comunicadoEditorContext";

const C = TV_DASHBOARD_HELP_TOOLTIPS.contextMenu;
const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

type Props = {
  open: boolean;
  position: FixedPanelPoint | null;
  onClose: () => void;
};

/**
 * Menu de contexto (botão direito) com tipografia do trecho selecionado
 * durante a edição inline — paridade com a ribbon Formatar.
 */
export function ComunicadoTextSelectionContextMenu({ open, position, onClose }: Props) {
  const {
    textEditSelectionStyle,
    toggleEditingTextRunStyle,
    applyEditingTextRunStylePatch,
    requestRibbonTab,
  } = useComunicadoEditor();

  const fontWeightActive =
    textEditSelectionStyle?.fontWeight === "bold" ||
    textEditSelectionStyle?.fontWeight === "mixed";
  const fontStyleActive =
    textEditSelectionStyle?.fontStyle === "italic" ||
    textEditSelectionStyle?.fontStyle === "mixed";
  const underlineActive =
    textEditSelectionStyle?.underline === true ||
    textEditSelectionStyle?.underline === "mixed";
  const strikethroughActive =
    textEditSelectionStyle?.strikethrough === true ||
    textEditSelectionStyle?.strikethrough === "mixed";

  function runToggle(key: "fontWeight" | "fontStyle" | "underline" | "strikethrough") {
    /* Mantém o menu aberto para empilhar B/I/U/S no mesmo trecho. */
    toggleEditingTextRunStyle(key);
  }

  function clearSelectionFormatting() {
    applyEditingTextRunStylePatch({
      fontWeight: "normal",
      fontStyle: "normal",
      textDecoration: "none",
      color: null,
      textHighlight: "transparent",
      fontFamily: null,
      fontSize: null,
    });
    onClose();
  }

  return (
    <ContextMenu
      open={open}
      position={position}
      onClose={onClose}
      aria-label={C.textSelectionMenu}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
    >
      <div
        {...{ [PRESERVE_TEXT_EDIT_FOCUS_ATTR]: "" }}
        onMouseDown={(event) => {
          /* Evita blur do contentEditable e perda do Range do trecho. */
          event.preventDefault();
        }}
      >
        <ContextMenuToolbar aria-label={C.textSelectionToolbar}>
          <ContextMenuToolbarButton
            label={H.bold}
            icon={Bold}
            active={Boolean(fontWeightActive)}
            onClick={() => runToggle("fontWeight")}
          />
          <ContextMenuToolbarButton
            label={H.italic}
            icon={Italic}
            active={Boolean(fontStyleActive)}
            onClick={() => runToggle("fontStyle")}
          />
          <ContextMenuToolbarButton
            label={H.underline}
            icon={Underline}
            active={Boolean(underlineActive)}
            onClick={() => runToggle("underline")}
          />
          <ContextMenuToolbarButton
            label={H.strikethrough}
            icon={Strikethrough}
            active={Boolean(strikethroughActive)}
            onClick={() => runToggle("strikethrough")}
          />
        </ContextMenuToolbar>
        <ContextMenuDivider />
        <ContextMenuItem
          label={H.clearFormatting}
          icon={RemoveFormatting}
          onSelect={clearSelectionFormatting}
        />
        <ContextMenuItem
          label={C.format}
          onSelect={() => {
            requestRibbonTab("format");
            onClose();
          }}
        />
      </div>
    </ContextMenu>
  );
}
