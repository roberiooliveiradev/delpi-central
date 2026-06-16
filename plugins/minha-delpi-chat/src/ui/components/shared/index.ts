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

export { IngestProgressIndicator } from "./IngestProgressIndicator";
