import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  listInteractionRooms,
  type InteractionInboxFilter,
  type InteractionRoomInboxItemDto,
} from "../../api/interactionRoomsApi";
import {
  CommercialActionButton,
  CommercialCatalogSearchBar,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialRoomInboxList,
  CommercialStateBanner,
  CommercialUnderlineNav,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import {
  buildInteractionRoomPath,
  buildPluginPath,
} from "../../app/pluginRoutes";
import { useInteractionInboxSync } from "../../app/CommercialRealtimeProvider";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

type Props = {
  basePath: string;
};

const FILTER_IDS: InteractionInboxFilter[] = [
  "all",
  "unread",
  "mentioned",
  "process",
  "wall",
];

function kindLabel(kind: string): string {
  if (kind === "process") return INTERACTION_ROOMS_CONTENT.kindProcess;
  if (kind === "wall") return INTERACTION_ROOMS_CONTENT.kindWall;
  return INTERACTION_ROOMS_CONTENT.kindEntity;
}

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

/** Inbox composta só com kit (RoomInboxList + search + filtros). */
export function InteractionRoomsInboxPage({ basePath }: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [filter, setFilter] = useState<InteractionInboxFilter>("all");
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<InteractionRoomInboxItemDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useInteractionInboxSync(
    () => setReloadKey((value) => value + 1),
    true,
  );

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void listInteractionRooms({
      filter,
      q: query.trim() || null,
      limit: 50,
      signal: controller.signal,
    })
      .then((rows) => {
        if (!controller.signal.aborted) setItems(rows);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : content.loadError);
        setItems([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filter, query, reloadKey, content.loadError]);

  const navItems = useMemo(
    () =>
      FILTER_IDS.map((id) => ({
        id,
        label: filterLabel(id),
        onSelect: () => setFilter(id),
      })),
    [],
  );

  const onSelect = useCallback(
    (roomId: string) => {
      const href = buildInteractionRoomPath(basePath, roomId);
      if (href) navigatePluginPath(href);
    },
    [basePath],
  );

  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{
          label: "Início",
          href: buildPluginPath("home", basePath),
        }}
        current={content.inboxTitle}
      />
      <CommercialPageHero
        title={content.inboxTitle}
        description={content.inboxSubtitle}
        actions={
          <CommercialActionButton
            variant="ghost"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            <RefreshCw size={16} aria-hidden="true" /> {content.reloadLabel}
          </CommercialActionButton>
        }
      />
      <CommercialUnderlineNav
        items={navItems}
        activeId={filter}
        aria-label={content.filtersAriaLabel}
      />
      <CommercialCatalogSearchBar
        value={query}
        onChange={setQuery}
        placeholder={content.searchPlaceholder}
        aria-label={content.searchPlaceholder}
      />
      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}
      {loading ? (
        <CommercialLoadingCard title={content.loadingLabel} variant="panel" />
      ) : null}
      {!loading && !error && items.length === 0 ? (
        <CommercialEmptyState
          title={content.inboxEmptyTitle}
          message={content.inboxEmptyDescription}
        />
      ) : null}
      {!loading && items.length > 0 ? (
        <CommercialRoomInboxList
          listAriaLabel={content.inboxListAriaLabel}
          emptyLabel={content.inboxEmptyTitle}
          unreadBadgeLabel={(count) =>
            content.unreadBadge.replace("{count}", String(count))
          }
          onSelect={onSelect}
          items={items.map((item) => ({
            id: item.id,
            title: item.title,
            preview: item.last_message_preview,
            metaLabel: item.last_message_at ?? undefined,
            kindLabel: kindLabel(item.kind),
            unreadCount: item.unread_count,
            mentioned: item.mentioned,
          }))}
        />
      ) : null}
    </section>
  );
}
