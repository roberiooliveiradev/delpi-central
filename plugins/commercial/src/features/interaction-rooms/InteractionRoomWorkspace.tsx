import { useCallback, useEffect, useMemo, useState } from "react";

import type { InteractionInboxFilter } from "../../api/interactionRoomsApi";
import {
  CommercialCatalogSearchBar,
  CommercialEmptyState,
  CommercialPageHero,
  CommercialPagePath,
  CommercialResizableColumns,
  CommercialUnderlineNav,
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

  const navItems = useMemo(
    () =>
      FILTER_IDS.map((id) => ({
        id,
        label: filterLabel(id),
        onSelect: () => {
          setFilter(id);
          replaceQuery(id, query);
        },
      })),
    [query, replaceQuery],
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
  ) : (
    <CommercialEmptyState
      title={content.selectRoomTitle}
      message={content.selectRoomDescription}
    />
  );

  return (
    <section className="cm-page-stack cm-room-workspace">
      <CommercialPagePath
        back={
          roomId
            ? { label: content.inboxTitle, href: listHref }
            : { label: "Início", href: buildPluginPath("home", basePath) }
        }
        current={content.inboxTitle}
      />
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
        <CommercialUnderlineNav
          items={navItems}
          activeId={filter}
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
        ) : (
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
        )}
      </div>
    </section>
  );
}
