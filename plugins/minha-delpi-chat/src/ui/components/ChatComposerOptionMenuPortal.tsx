import type { ReactNode, RefObject } from "react";

import { AnchoredMenuPortal } from "./shared/overlay/AnchoredMenuPortal";

type ChatComposerOptionMenuPortalProps = {
  open: boolean;
  triggerRef: RefObject<HTMLElement | null>;
  itemCount: number;
  menuLabel: string;
  onClose: () => void;
  children: ReactNode;
};

/** @deprecated Prefer ComposerOptionSelector ou AnchoredMenuPortal diretamente. */
export function ChatComposerOptionMenuPortal(props: ChatComposerOptionMenuPortalProps) {
  return <AnchoredMenuPortal placement="composer-option" {...props} />;
}
