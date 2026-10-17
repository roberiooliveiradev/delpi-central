import { ConversationSidebar } from "./ConversationSidebar";
import type { ConversationSidebarProps } from "./ConversationSidebar";

export type ConversationNavigationItem = {
  id: string;
  title: string;
  active?: boolean;
};

export type ConversationNavigationProps = Omit<
  ConversationSidebarProps,
  "history" | "pinnedHistory" | "olderHistory" | "historyStatus" | "collapsed"
> & {
  /** Explicitly authorized history projection; never inferred from turns. */
  recent?: readonly ConversationNavigationItem[];
  pinned?: readonly ConversationNavigationItem[];
  older?: readonly ConversationNavigationItem[];
  status?: "unavailable" | "ready" | "loading" | "authorized_empty" | "error";
};

/**
 * The conversation-category body reuses the established sidebar actions and
 * rows. No history provider, search index, session creation or permission logic.
 * A host may enable selection only after it has an authorized backend contract.
 */
export function ConversationNavigation({
  recent,
  pinned,
  older,
  status = "unavailable",
  ...actions
}: ConversationNavigationProps) {
  return (
    <ConversationSidebar
      {...actions}
      history={recent}
      pinnedHistory={pinned}
      olderHistory={older}
      historyStatus={status}
    />
  );
}
