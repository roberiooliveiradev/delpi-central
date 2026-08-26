import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState, type MouseEvent } from "react";

import {
  listInteractionRooms,
  type InteractionInboxFilter,
  type InteractionRoomInboxItemDto,
} from "../../api/interactionRoomsApi";
import {
  CommercialActionButton,
  CommercialCatalogSearchBar,
  CommercialEmptyGuidance,
  CommercialLoadingCard,
  CommercialRoomInboxList,
  CommercialRoomInboxPanel,
  CommercialScopeChipBar,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialViewTransition,
} from "../../app/commercialUi";
import { markdownToPlainPreview } from "@delpi/plugin-ui/index";
import {
  buildCustomerDetailHref,
  navigatePluginPath,
} from "../../app/pluginNavigation";
import { buildInteractionRoomPath } from "../../app/pluginRoutes";
import { useInteractionInboxSync } from "../../app/CommercialRealtimeProvider";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { accountLinkTitle } from "../../content/entityLinkHints";
import { CustomerAvatar } from "../customers/components/CustomerAvatar";
import {
  customerAvatarKey,
  useCustomerAvatarPresence,
} from "../../hooks/useCustomerAvatarPresence";
import { formatInboxMetaLabel } from "./formatInboxMetaLabel";
import { inboxCustomerAvatarName } from "./inboxCustomerAvatarName";

type Props = {
  basePath: string;
  selectedRoomId?: string | null;
  variant?: "page" | "pane";
  filter?: InteractionInboxFilter;
  query?: string;
  onFilterChange?: (filter: InteractionInboxFilter) => void;
  onQueryChange?: (query: string) => void;
  onSelectedRoomTitle?: (title: string | null) => void;
  preserveSearch?: string;
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

function inboxEmptyCopy(
  filter: InteractionInboxFilter,
): { title: string; message: string } {
  const content = INTERACTION_ROOMS_CONTENT;
  switch (filter) {
    case "unread":
      return {
        title: content.inboxFilterEmptyUnreadTitle,
        message: content.inboxFilterEmptyUnreadDescription,
      };
    case "mentioned":
      return {
        title: content.inboxFilterEmptyMentionedTitle,
        message: content.inboxFilterEmptyMentionedDescription,
      };
    case "process":
      return {
        title: content.inboxFilterEmptyProcessTitle,
        message: content.inboxFilterEmptyProcessDescription,
      };
    case "wall":
      return {
        title: content.inboxFilterEmptyWallTitle,
        message: content.inboxFilterEmptyWallDescription,
      };
    default:
      return {
        title: content.inboxEmptyTitle,
        message: content.inboxEmptyDescription,
      };
  }
}

function customerIdentity(item: InteractionRoomInboxItemDto): {
  code: string;
  store: string;
  name: string;
} | null {
  const code = (item.customer_code ?? "").trim();
  const store = (item.customer_store ?? "").trim();
  if (!code || !store) return null;
  const name = inboxCustomerAvatarName(item) || code;
  return { code, store, name };
}

/** Inbox composta só com kit (RoomInboxList + search + filtros). */
export function InteractionRoomsInboxPage({
  basePath,
  selectedRoomId = null,
  filter: filterProp,
  query: queryProp,
  onFilterChange,
  onQueryChange,
  onSelectedRoomTitle,
  preserveSearch = "",
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [filterState, setFilterState] = useState<InteractionInboxFilter>("all");
  const [queryState, setQueryState] = useState("");
  const filter = filterProp ?? filterState;
  const query = queryProp ?? queryState;
  const setFilter = onFilterChange ?? setFilterState;
  const setQuery = onQueryChange ?? setQueryState;
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

  const filterChips = useMemo(
    () =>
      FILTER_IDS.map((id) => ({
        id,
        label: filterLabel(id),
        active: id === filter,
        onSelect: () => setFilter(id),
      })),
    [filter, setFilter],
  );

  useEffect(() => {
    if (!selectedRoomId) return;
    const hit = items.find((item) => item.id === selectedRoomId);
    onSelectedRoomTitle?.(hit?.title ?? null);
  }, [items, selectedRoomId, onSelectedRoomTitle]);

  const itemsById = useMemo(
    () => new Map(items.map((item) => [item.id, item])),
    [items],
  );

  const avatarPairs = useMemo(
    () =>
      items.flatMap((item) => {
        const identity = customerIdentity(item);
        if (!identity) return [];
        return [
          {
            customer_code: identity.code,
            customer_store: identity.store,
          },
        ];
      }),
    [items],
  );
  const avatarByKey = useCustomerAvatarPresence(avatarPairs);

  const onSelect = useCallback(
    (roomId: string) => {
      const href = buildInteractionRoomPath(basePath, roomId);
      if (href) navigatePluginPath(`${href}${preserveSearch}`);
    },
    [basePath, preserveSearch],
  );

  const onCustomerNavigate = useCallback(
    (event: MouseEvent<HTMLAnchorElement>, href: string) => {
      event.stopPropagation();
      event.preventDefault();
      navigatePluginPath(href);
    },
    [],
  );

  const inboxEmpty = inboxEmptyCopy(filter);

  return (
    <section className="cm-room-inbox-pane">
      <CommercialSectionCard
        className="cm-room-inbox-pane__toolbar"
        title={content.inboxToolbarTitle}
      >
        <div className="cm-room-inbox-pane__filters">
          <div className="cm-room-inbox-search">
            <CommercialCatalogSearchBar
              value={query}
              onChange={setQuery}
              placeholder={content.searchPlaceholder}
              aria-label={content.searchPlaceholder}
            />
          </div>
          <CommercialScopeChipBar
            chips={filterChips}
            aria-label={content.filtersAriaLabel}
          />
        </div>
      </CommercialSectionCard>
      {error ? (
        <CommercialStateBanner variant="error">
          {error}{" "}
          <CommercialActionButton
            variant="ghost"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            <RefreshCw size={16} aria-hidden="true" /> {content.reloadLabel}
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}
      <div className="cm-room-inbox-pane__body">
      <CommercialViewTransition
        transitionKey={`${filter}:${query.trim()}`}
        tone="panel"
      >
      <CommercialRoomInboxPanel aria-label={content.inboxListAriaLabel}>
      {loading ? (
        <CommercialLoadingCard title={content.loadingLabel} variant="panel" />
      ) : null}
      {!loading && !error && items.length === 0 ? (
        <CommercialEmptyGuidance
          variant="panel"
          title={inboxEmpty.title}
          message={inboxEmpty.message}
        />
      ) : null}
      {!loading && items.length > 0 ? (
        <CommercialRoomInboxList
          listAriaLabel={content.inboxListAriaLabel}
          emptyLabel={inboxEmpty.title}
          emptyContent={
            <CommercialEmptyGuidance
              variant="panel"
              title={inboxEmpty.title}
              message={inboxEmpty.message}
            />
          }
          unreadBadgeLabel={(count) =>
            content.unreadBadge.replace("{count}", String(count))
          }
          onSelect={onSelect}
          leading={(row) => {

            const dto = itemsById.get(row.id);
            if (!dto) return null;
            const identity = customerIdentity(dto);
            const avatarName = inboxCustomerAvatarName(dto);
            if (!identity) {
              return (
                <CustomerAvatar
                  code=""
                  store=""
                  name={avatarName}
                  size="sm"
                  previewable={false}
                />
              );
            }
            const href = buildCustomerDetailHref(identity.code, identity.store, {
              basePath,
            });
            const hasAvatar =
              avatarByKey.get(
                customerAvatarKey(identity.code, identity.store),
              ) === true;
            if (!href) {
              return (
                <CustomerAvatar
                  code={identity.code}
                  store={identity.store}
                  name={identity.name}
                  hasAvatar={hasAvatar}
                  size="sm"
                  previewable={false}
                />
              );
            }
            return (
              <CustomerAvatar
                code={identity.code}
                store={identity.store}
                name={identity.name}
                hasAvatar={hasAvatar}
                size="sm"
                href={href}
                title={accountLinkTitle(identity.name)}
                onNavigate={(event) => onCustomerNavigate(event, href)}
              />
            );
          }}
          subtitle={(row) => {
            const dto = itemsById.get(row.id);
            const name = (dto?.customer_name ?? "").trim();
            return name || kindLabel(dto?.kind ?? "entity");
          }}
          items={items.map((item) => ({
            id: item.id,
            title: item.title,
            preview: markdownToPlainPreview(item.last_message_preview ?? ""),
            metaLabel: formatInboxMetaLabel(item.last_message_at, {
              yesterdayLabel: content.inboxMetaYesterday,
            }),
            kindLabel: kindLabel(item.kind),
            unreadCount: item.unread_count,
            mentioned: item.mentioned,
            selected: Boolean(selectedRoomId) && item.id === selectedRoomId,
          }))}
        />
      ) : null}
      </CommercialRoomInboxPanel>
      </CommercialViewTransition>
      </div>
    </section>
  );
}
