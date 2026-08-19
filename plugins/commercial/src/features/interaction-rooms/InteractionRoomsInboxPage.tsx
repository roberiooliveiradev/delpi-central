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
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialRoomInboxList,
  CommercialStateBanner,
  CommercialUnderlineNav,
} from "../../app/commercialUi";
import {
  buildCustomerDetailHref,
  navigatePluginPath,
} from "../../app/pluginNavigation";
import {
  buildInteractionRoomPath,
  buildPluginPath,
} from "../../app/pluginRoutes";
import { useInteractionInboxSync } from "../../app/CommercialRealtimeProvider";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
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
  variant = "page",
  filter: filterProp,
  query: queryProp,
  onFilterChange,
  onQueryChange,
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

  const navItems = useMemo(
    () =>
      FILTER_IDS.map((id) => ({
        id,
        label: filterLabel(id),
        onSelect: () => setFilter(id),
      })),
    [],
  );

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

  const chrome = variant === "page";

  return (
    <section className={chrome ? "cm-page-stack" : "cm-room-inbox-pane"}>
      {chrome ? (
        <CommercialPagePath
          back={{
            label: "Início",
            href: buildPluginPath("home", basePath),
          }}
          current={content.inboxTitle}
        />
      ) : null}
      {chrome ? (
        <CommercialPageHero
          title={content.inboxTitle}
          description={content.inboxSubtitle}
          actions={
            <div className="cm-room-inbox-search">
              <CommercialCatalogSearchBar
                value={query}
                onChange={setQuery}
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
      ) : null}
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
                title={identity.name}
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
            preview: item.last_message_preview,
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
    </section>
  );
}
