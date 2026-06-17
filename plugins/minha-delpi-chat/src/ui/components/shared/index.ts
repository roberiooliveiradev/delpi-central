export { AnchoredMenuPortal } from "./overlay/AnchoredMenuPortal";
export { useAnchoredMenuLayout } from "./overlay/useAnchoredMenuLayout";
export type { AnchoredMenuPlacement, MenuPortalSource } from "./overlay/useAnchoredMenuLayout";
export type { AnchoredMenuPortalProps } from "./overlay/AnchoredMenuPortal";

export { ModalPortal } from "./overlay/ModalPortal";
export {
  MDC_MODAL_ROOT_ID,
  isOverlayPortalContained,
  resolveModalPortalContainer,
  resolveOverlayPortalContainer,
} from "./overlay/modalPortalTarget";

export { ComposerOptionSelector } from "./composer/ComposerOptionSelector";
export type { ComposerOptionItem } from "./composer/ComposerOptionSelector";

export { ChatInputPlusMenu } from "./composer/ChatInputPlusMenu";

export { ChatModal } from "./modal/ChatModal";
export type { ChatModalMobileLayout, ChatModalSize } from "./modal/ChatModal";

export { ChatConfirmDialog } from "./modal/ChatConfirmDialog";
export { ChatAlertDialog } from "./modal/ChatAlertDialog";
export { ChatPromptDialog } from "./modal/ChatPromptDialog";
export { ChatShortcutPromptDialog } from "./modal/ChatShortcutPromptDialog";
export { useConfirmDialog } from "./modal/useConfirmDialog";
export { useAlertDialog } from "./modal/useAlertDialog";
export { usePromptDialog } from "./modal/usePromptDialog";
export {
  ChatMemoryUsedDialog,
  type MemoryUsageView,
} from "./modal/ChatMemoryUsedDialog";

export {
  COMPOSER_PANEL_ANCHOR_GAP,
  estimateChatInputPlusMenuItemCount,
  menuAnchorRectFromElement,
  resolveComposerPanelMenuPosition,
} from "./overlay/menuPositionUtils";
export type { ComposerOptionMenuLayout, MenuAnchorRect } from "./overlay/menuPositionUtils";

export { ActionMenuPanel } from "./menus/ActionMenuPanel";
export type { ActionMenuItem } from "./menus/ActionMenuPanel";

export { DropdownMenuTrigger } from "./menus/DropdownMenuTrigger";

export {
  ChatTableRowMenu,
  estimateMenuHeight,
  type TableRowMenuAnchor,
} from "./menus/ChatTableRowMenu";

export { IngestProgressIndicator } from "./IngestProgressIndicator";
