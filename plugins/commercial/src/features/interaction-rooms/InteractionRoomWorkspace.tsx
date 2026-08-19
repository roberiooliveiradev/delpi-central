import { useCallback, useEffect, useMemo, useState } from "react";

import type { InteractionInboxFilter } from "../../api/interactionRoomsApi";
import {
  CommercialCatalogSearchBar,
  CommercialPageHero,
  CommercialPagePath,
  CommercialResizableColumns,
  CommercialScopeChipBar,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import {
  buildInteractionRoomPath,
  buildInteractionRoomsPath,
  buildPluginPath,
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

const FILTER_IDS: InteractionInboxFilter[] = [
  "all",
  "unread",
  "mentioned",
  "process",
  "wall",
];

function filterLabel(id: InteractionInboxFilter): string {
  const map: Record<string, string> = {
    all: INTERACTION_ROOMS_CONTENT.filterAll,
    unread: INTERACTION_ROOMS_CONTENT.filterUnread,
    mentioned: INTERACTION_ROOMS_CONTENT.filterMentioned,
    process: INTERACTION_ROOMS_CONTENT.filterProcess,
    wall: INTERACTION_ROOMS_CONTENT.filterWall,
  };
  return map[id] ?? String(id);
}

export function InteractionRoomWorkspace({
  basePath,
  roomId = null,
  search,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const parsed = parseInteractionRoomSearch(search);
  const [filter, setFilter] = useState<InteractionInboxFilter>(parsed.filter);
  const [query, setQuery] = useState(parsed.q);
  const [openRoomTitle, setOpenRoomTitle] = useState<string | null>(null);

  useEffect(() => {
    const next = parseInteractionRoomSearch(search);
    setFilter(next.filter);
    setQuery(next.q);
  }, [search]);

  useEffect(() => {
    if (!roomId) setOpenRoomTitle(null);
  }, [roomId]);

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

  const filterChips = useMemo(
    () =>
      FILTER_IDS.map((id) => ({
        id,
        label: filterLabel(id),
        active: id === filter,
        onSelect: () => {
          setFilter(id);
          replaceQuery(id, query);
        },
      })),
    [filter, query, replaceQuery],
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
      onSelectedRoomTitle={setOpenRoomTitle}
      preserveSearch={roomSearch}
    />
  );
  const thread = roomId ? (
    <InteractionRoomPage
      basePath={basePath}
      roomId={roomId}
      variant="pane"
      inboxHref={listHref}
      onRoomTitle={setOpenRoomTitle}
    />
  ) : null;

  const pathCurrent = roomId
    ? openRoomTitle || content.roomFallbackTitle
    : content.inboxTitle;
  const pathBack = roomId
    ? { label: content.inboxTitle, href: listHref }
    : { label: "Início", href: buildPluginPath("home", basePath) };

  return (
    <section className="cm-page-stack cm-room-workspace">
      <CommercialPagePath back={pathBack} current={pathCurrent} />
      <CommercialPageHero
        density="compact"
        title={content.inboxTitle}
        description={content.inboxSubtitle}
        actions={
          <div className="cm-room-inbox-search">
            <CommercialCatalogSearchBar
              value={query}
              onChange={(value) => {
                setQuery(value);
                replaceQuery(filter, value);
              }}
              placeholder={content.searchPlaceholder}
              aria-label={content.searchPlaceholder}
            />
          </div>
        }
      >
        <CommercialScopeChipBar
          chips={filterChips}
          aria-label={content.filtersAriaLabel}
        />
      </CommercialPageHero>
      <div className="cm-room-workspace__grid">
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
      </div>
    </section>
  );
}
