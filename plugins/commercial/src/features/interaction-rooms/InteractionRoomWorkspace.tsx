import { useCallback, useEffect, useState } from "react";

import type { InteractionInboxFilter } from "../../api/interactionRoomsApi";
import { CommercialResizableColumns, CommercialStateBanner, CommercialViewTransition } from "../../app/commercialUi";
import { useCommercialRealtime } from "../../app/CommercialRealtimeProvider";
import { navigatePluginPath } from "../../app/pluginNavigation";
import {
  buildInteractionRoomPath,
  buildInteractionRoomsPath,
} from "../../app/pluginRoutes";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { InteractionRoomPage } from "./InteractionRoomPage";
import { InteractionRoomsInboxPage } from "./InteractionRoomsInboxPage";
import {
  buildInteractionRoomSearch,
  parseInteractionRoomSearch,
} from "./interactionRoomSearch";
import {
  readInboxCollapsed,
  readInboxWidthPx,
  writeInboxCollapsed,
  writeInboxWidthPx,
} from "./interactionRoomSplitStorage";
import { useMatchMedia } from "./useMatchMedia";

type Props = {
  basePath: string;
  roomId?: string | null;
  search?: string;
};

export function InteractionRoomWorkspace({
  basePath,
  roomId = null,
  search,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const { connectionError } = useCommercialRealtime();
  const parsed = parseInteractionRoomSearch(search);
  const [filter, setFilter] = useState<InteractionInboxFilter>(parsed.filter);
  const [query, setQuery] = useState(parsed.q);

  useEffect(() => {
    const next = parseInteractionRoomSearch(search);
    setFilter(next.filter);
    setQuery(next.q);
  }, [search]);

  const roomSearch = buildInteractionRoomSearch({ filter, q: query });
  const listHref = `${buildInteractionRoomsPath(basePath)}${roomSearch}`;
  const stacked = useMatchMedia("(max-width: 899px)");
  const [leftWidth, setLeftWidth] = useState<number | undefined>(() =>
    readInboxWidthPx(),
  );
  const [collapsed, setCollapsed] = useState(() => readInboxCollapsed());

  const replaceQuery = useCallback(
    (nextFilter: InteractionInboxFilter, nextQuery: string) => {
      const qs = buildInteractionRoomSearch({ filter: nextFilter, q: nextQuery });
      const path = roomId
        ? buildInteractionRoomPath(basePath, roomId)
        : buildInteractionRoomsPath(basePath);
      if (path) navigatePluginPath(`${path}${qs}`, { replace: true });
    },
    [basePath, roomId],
  );

  const inbox = (
    <InteractionRoomsInboxPage
      basePath={basePath}
      variant="pane"
      selectedRoomId={roomId}
      filter={filter}
      query={query}
      onFilterChange={(next) => {
        setFilter(next);
        replaceQuery(next, query);
      }}
      onQueryChange={(next) => {
        setQuery(next);
        replaceQuery(filter, next);
      }}
      preserveSearch={roomSearch}
    />
  );
  const thread = roomId ? (
    <InteractionRoomPage
      basePath={basePath}
      roomId={roomId}
      variant="pane"
      inboxHref={listHref}
    />
  ) : null;

  return (
    <section className="cm-room-workspace">
      {connectionError ? (
        <CommercialStateBanner variant="warning">
          {content.roomConnectionErrorBanner}
        </CommercialStateBanner>
      ) : null}
      <div className="cm-room-workspace__grid">
        <CommercialViewTransition
          transitionKey={
            stacked
              ? roomId ?? "inbox"
              : roomId
                ? `split-${roomId}`
                : "inbox-full"
          }
          tone="page"
        >
          {stacked ? (
            roomId ? (
              thread
            ) : (
              inbox
            )
          ) : roomId ? (
            <CommercialResizableColumns
              left={inbox}
              right={thread}
              leftWidthPx={leftWidth}
              collapsed={collapsed}
              onLeftWidthChange={(widthPx) => {
                setLeftWidth(widthPx);
                writeInboxWidthPx(widthPx);
              }}
              onCollapsedChange={(next) => {
                setCollapsed(next);
                writeInboxCollapsed(next);
              }}
              labels={{
                separatorAriaLabel: content.inboxResizeAriaLabel,
                collapseAriaLabel: content.inboxCollapseAriaLabel,
                expandAriaLabel: content.inboxExpandAriaLabel,
              }}
            />
          ) : (
            inbox
          )}
        </CommercialViewTransition>
      </div>
    </section>
  );
}
