import { RefreshCw, Trash2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState, type MouseEvent } from "react";

import {
  deleteInteractionRoom,
  listInteractionRooms,
  type InteractionInboxFilter,
  type InteractionRoomInboxItemDto,
} from "../../api/interactionRoomsApi";
import {
  CommercialActionButton,
  CommercialCatalogSearchBar,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialRoomInboxList,
  CommercialScopeChipBar,
  CommercialSectionCard,
  CommercialStateBanner,
} from "../../app/commercialUi";
import { markdownToPlainPreview } from "@delpi/plugin-ui/index";
import {
  buildCustomerDetailHref,
  navigatePluginPath,
} from "../../app/pluginNavigation";
import { buildInteractionRoomPath, buildInteractionRoomsPath } from "../../app/pluginRoutes";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { usePortfolioScope } from "../../app/usePortfolioScope";
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
  const { canManagePortfolios } = usePortfolioScope();
  const confirm = useCommercialConfirm();
  const { notifySuccess, notifyError } = useCommercialFloatingNotice();
  const [deletingRoomId, setDeletingRoomId] = useState<string | null>(null);
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

  const onDeleteRoom = useCallback(
    async (roomId: string) => {
      if (!canManagePortfolios || !roomId.trim() || deletingRoomId) return;
      const ok = await confirm({
        title: content.deleteRoomConfirmTitle,
        message: content.deleteRoomConfirmMessage,
        confirmLabel: content.deleteRoomConfirmLabel,
        cancelLabel: content.deleteRoomCancelLabel,
        variant: "danger",
      });
      if (!ok) return;
      setDeletingRoomId(roomId);
      try {
        await deleteInteractionRoom(roomId);
        setItems((prev) => prev.filter((item) => item.id !== roomId));
        notifySuccess(content.deleteRoomOk);
        if (selectedRoomId && selectedRoomId === roomId) {
          const href = buildInteractionRoomsPath(basePath);
          if (href) navigatePluginPath(`${href}${preserveSearch}`);
        }
      } catch (err: unknown) {
        notifyError(err instanceof Error ? err.message : content.deleteRoomError);
      } finally {
        setDeletingRoomId(null);
      }
    },
    [
      canManagePortfolios,
      deletingRoomId,
      confirm,
      content.deleteRoomConfirmTitle,
      content.deleteRoomConfirmMessage,
      content.deleteRoomConfirmLabel,
      content.deleteRoomCancelLabel,
      content.deleteRoomOk,
      content.deleteRoomError,
      notifySuccess,
      notifyError,
      selectedRoomId,
      basePath,
      preserveSearch,
    ],
  );

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
          actions={
            canManagePortfolios
              ? (row) => (
                  <CommercialActionButton
                    variant="ghost"
                    aria-label={content.deleteRoomActionLabel}
                    title={content.deleteRoomActionLabel}
                    disabled={deletingRoomId === row.id}
                    onClick={() => {
                      void onDeleteRoom(row.id);
                    }}
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </CommercialActionButton>
                )
              : undefined
          }
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
      </div>
    </section>
  );
}
