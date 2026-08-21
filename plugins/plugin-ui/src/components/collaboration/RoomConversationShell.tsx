import type {
  ElementType,
  ReactNode,
  Ref,
  UIEventHandler,
} from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  ConversationFileDropLayer,
  conversationFileDropLayerBemClasses,
  type ConversationFileDropLayerClassNames,
} from "./ConversationFileDropLayer";

export type RoomConversationShellClassNames = {
  root: string;
  header: string;
  body: string;
  main: string;
  stage: string;
  msgs: string;
  dock: string;
  panel: string;
};

export function roomConversationShellBemClasses(
  prefix: string,
): RoomConversationShellClassNames {
  const base = `${prefix}-room-thread`;
  const ui = "delpi-ui-room-thread";
  const panelBase = `${prefix}-room-panel`;
  const panelUi = "delpi-ui-room-panel";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    header: pair(`${base}__header`, `${ui}__header`),
    body: pair(`${base}__body`, `${ui}__body`),
    main: pair(`${base}__main`, `${ui}__main`),
    stage: pair(`${base}__stage`, `${ui}__stage`),
    msgs: pair(`${base}__msgs`, `${ui}__msgs`),
    dock: pair(`${base}__dock`, `${ui}__dock`),
    panel: pair(panelBase, panelUi),
  };
}

export type RoomConversationChatColumnProps = {
  classNames: Pick<RoomConversationShellClassNames, "stage" | "msgs" | "dock">;
  msgsRef?: Ref<HTMLDivElement | null>;
  onMsgsScroll?: UIEventHandler<HTMLDivElement>;
  children: ReactNode;
  dock: ReactNode;
};

/**
 * Stage + msgs + dock — chat column shared by room page and embed cards.
 * Dock lives inside stage so flex pins the composer to the bottom even when
 * an intermediate parent (tabpanel / view-transition) is not a flex column.
 */
export function RoomConversationChatColumn({
  classNames,
  msgsRef,
  onMsgsScroll,
  children,
  dock,
}: RoomConversationChatColumnProps) {
  return (
    <div className={classNames.stage}>
      <div
        className={classNames.msgs}
        ref={msgsRef}
        onScroll={onMsgsScroll}
      >
        {children}
      </div>
      <div className={classNames.dock}>{dock}</div>
    </div>
  );
}

export type RoomConversationShellProps = {
  classNames: RoomConversationShellClassNames;
  dropClassNames: ConversationFileDropLayerClassNames;
  rootClassName?: string;
  as?: ElementType;
  /**
   * When false, render only the drop + header/body (parent already has
   * the thread root for alerts/loading chrome).
   */
  wrapRoot?: boolean;
  dropOverlayLabel: string;
  accept: string;
  onFiles: (files: File[]) => void;
  header: ReactNode;
  main: ReactNode;
  sidePanel?: ReactNode;
  afterHeader?: ReactNode;
};

/**
 * Canonical conversation chrome: drop layer + room thread
 * (`__header` / `__body` / `__main` [+ side panel]).
 */
export function RoomConversationShell({
  classNames,
  dropClassNames,
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
}: RoomConversationShellProps) {
  const drop = (
    <ConversationFileDropLayer
      classNames={dropClassNames}
      overlayLabel={dropOverlayLabel}
      accept={accept}
      onFiles={onFiles}
    >
      <div className={classNames.header}>{header}</div>
      {afterHeader}
      <div className={classNames.body}>
        <div className={classNames.main}>{main}</div>
        {sidePanel}
      </div>
    </ConversationFileDropLayer>
  );

  if (!wrapRoot) return drop;
  const className = [classNames.root, rootClassName].filter(Boolean).join(" ");
  return <Root className={className}>{drop}</Root>;
}

export type RoomPanelProps = {
  classNames: Pick<RoomConversationShellClassNames, "panel">;
  children: ReactNode;
  "aria-label"?: string;
};

/** Framed surface for embedding a room thread on object detail cards. */
export function RoomPanel({
  classNames,
  children,
  "aria-label": ariaLabel,
}: RoomPanelProps) {
  return (
    <div className={classNames.panel} role="region" aria-label={ariaLabel}>
      {children}
    </div>
  );
}

export type DashboardRoomConversationShellProps = Omit<
  RoomConversationShellProps,
  "classNames" | "dropClassNames"
>;

export type DashboardRoomConversationChatColumnProps = Omit<
  RoomConversationChatColumnProps,
  "classNames"
>;

export type DashboardRoomPanelProps = Omit<RoomPanelProps, "classNames">;

export function createDashboardRoomConversationShell(prefix: string) {
  const classNames = roomConversationShellBemClasses(prefix);
  const dropClassNames = conversationFileDropLayerBemClasses(prefix);

  function DashboardRoomConversationShell(
    props: DashboardRoomConversationShellProps,
  ) {
    return (
      <RoomConversationShell
        classNames={classNames}
        dropClassNames={dropClassNames}
        {...props}
      />
    );
  }

  function DashboardRoomConversationChatColumn(
    props: DashboardRoomConversationChatColumnProps,
  ) {
    return <RoomConversationChatColumn classNames={classNames} {...props} />;
  }

  function DashboardRoomPanel(props: DashboardRoomPanelProps) {
    return <RoomPanel classNames={classNames} {...props} />;
  }

  return {
    Shell: DashboardRoomConversationShell,
    ChatColumn: DashboardRoomConversationChatColumn,
    Panel: DashboardRoomPanel,
    classNames,
  };
}
