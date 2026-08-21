import type {
  ReactNode,
  Ref,
  UIEventHandler,
} from "react";

import { CommercialConversationFileDropLayer } from "../../app/commercialUi";

export type InteractionRoomConversationChatColumnProps = {
  msgsRef?: Ref<HTMLDivElement | null>;
  onMsgsScroll?: UIEventHandler<HTMLDivElement>;
  /** EmptyState or MessageThread inside `__msgs`. */
  children: ReactNode;
  /** Composer (and related) inside `__dock`. */
  dock: ReactNode;
};

/**
 * Stage + msgs + dock — shared chat column used by Panel and Page (chat tab).
 */
export function InteractionRoomConversationChatColumn({
  msgsRef,
  onMsgsScroll,
  children,
  dock,
}: InteractionRoomConversationChatColumnProps) {
  return (
    <>
      <div className="cm-room-thread__stage">
        <div
          className="cm-room-thread__msgs"
          ref={msgsRef}
          onScroll={onMsgsScroll}
        >
          {children}
        </div>
      </div>
      <div className="cm-room-thread__dock">{dock}</div>
    </>
  );
}

export type InteractionRoomConversationShellProps = {
  /** Extra classes on the thread root (e.g. `cm-page-stack`). */
  rootClassName?: string;
  /** Page uses `section`; embed defaults to `div`. */
  as?: "div" | "section";
  /**
   * When false, render only the drop + header/body (parent already has
   * `cm-room-thread` for alerts/loading chrome).
   */
  wrapRoot?: boolean;
  dropOverlayLabel: string;
  accept: string;
  onFiles: (files: File[]) => void;
  /** RoomHeader (nav/actions stay in the consumer). */
  header: ReactNode;
  /** Content of `__main` (chat column, ViewTransition, shared view, …). */
  main: ReactNode;
  /** Sibling of `__main` inside `__body` (side panel on the page). */
  sidePanel?: ReactNode;
  /** Nodes between header and body (e.g. rename dialog on the page). */
  afterHeader?: ReactNode;
};

/**
 * Canonical conversation chrome: drop layer + `cm-room-thread`
 * (`__header` / `__body` / `__main` [+ side panel]).
 */
export function InteractionRoomConversationShell({
  rootClassName,
  as: Root = "div",
  wrapRoot = true,
  dropOverlayLabel,
  accept,
  onFiles,
  header,
  main,
  sidePanel,
  afterHeader,
}: InteractionRoomConversationShellProps) {
  const drop = (
    <CommercialConversationFileDropLayer
      overlayLabel={dropOverlayLabel}
      accept={accept}
      onFiles={onFiles}
    >
      <div className="cm-room-thread__header">{header}</div>
      {afterHeader}
      <div className="cm-room-thread__body">
        <div className="cm-room-thread__main">{main}</div>
        {sidePanel}
      </div>
    </CommercialConversationFileDropLayer>
  );
  if (!wrapRoot) return drop;
  const className = ["cm-room-thread", rootClassName].filter(Boolean).join(" ");
  return <Root className={className}>{drop}</Root>;
}
