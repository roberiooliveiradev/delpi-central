import { useEffect, useState } from "react";

import {
  resolveInteractionRoom,
  type InteractionRoomDto,
} from "../../api/interactionRoomsApi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import {
  CommercialActionButton,
  CommercialHostDrawer,
  CommercialLoadingCard,
  CommercialRoomPanel,
  CommercialSectionCard,
  CommercialStateBanner,
} from "../../app/commercialUi";
import { buildInteractionRoomPath } from "../../app/pluginRoutes";
import { CM_HELP } from "../../content/helpTooltips";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { InteractionRoomPage } from "./InteractionRoomPage";
import {
  INTERACTION_ROOM_NARROW_QUERY,
  useMatchMedia,
} from "./useMatchMedia";

type Props = {
  basePath: string;
  entityType: string;
  entityKey: string | null;
  roomTitle: string;
};

/**
 * Painel embutido na ficha — resolve lazy e monta só a thread da sala
 * (topbar + mensagens + composer), sem a listagem de conversas.
 * Viewport ≤768px: conversa no drawer host-contained.
 */
export function InteractionRoomPanel({
  basePath,
  entityType,
  entityKey,
  roomTitle,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const narrow = useMatchMedia(INTERACTION_ROOM_NARROW_QUERY);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [room, setRoom] = useState<InteractionRoomDto | null>(null);
  const [loading, setLoading] = useState(Boolean(entityKey));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const key = entityKey?.trim() ?? "";
    if (!key) {
      setLoading(false);
      setRoom(null);
      setError(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void (async () => {
      try {
        const resolved = await resolveInteractionRoom(
          {
            kind: "entity",
            entity_type: entityType,
            entity_key: key,
            title: roomTitle,
          },
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setRoom(resolved);
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof Error ? err.message : content.panelResolveError,
        );
        setRoom(null);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [entityType, entityKey, roomTitle, content.panelResolveError]);

  useEffect(() => {
    if (!narrow) setDrawerOpen(false);
  }, [narrow]);

  const openHref =
    room?.id != null
      ? buildInteractionRoomPath(basePath, room.id)
      : null;

  const openRoomAction =
    openHref != null ? (
      <CommercialActionButton
        variant="ghost"
        onClick={() => navigatePluginPath(openHref)}
      >
        {content.panelOpenRoom}
      </CommercialActionButton>
    ) : null;

  const roomBody =
    !loading && room?.id ? (
      <CommercialRoomPanel aria-label={content.panelTitle}>
        <InteractionRoomPage
          basePath={basePath}
          roomId={room.id}
          variant="pane"
        />
      </CommercialRoomPanel>
    ) : null;

  const statusBlock = (
    <>
      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}
      {loading ? (
        <CommercialLoadingCard title={content.panelLoadingLabel} variant="panel" />
      ) : null}
    </>
  );

  const sectionCardProps = {
    title: content.panelTitle,
    hint: CM_HELP.interactionRooms.panel,
    collapsible: true as const,
    defaultOpen: true as const,
  };

  if (!entityKey?.trim()) {
    return (
      <CommercialSectionCard {...sectionCardProps}>
        <CommercialStateBanner variant="warning">
          {content.panelMissingKey}
        </CommercialStateBanner>
      </CommercialSectionCard>
    );
  }

  if (narrow) {
    return (
      <>
        <CommercialSectionCard {...sectionCardProps} actions={openRoomAction}>
          <p>{content.panelNarrowHint}</p>
          <CommercialActionButton
            variant="primary"
            onClick={() => setDrawerOpen(true)}
          >
            {content.panelOpenDrawer}
          </CommercialActionButton>
        </CommercialSectionCard>
        <CommercialHostDrawer
          open={drawerOpen}
          title={room?.title || roomTitle || content.panelTitle}
          onClose={() => setDrawerOpen(false)}
          closeAriaLabel={content.drawerCloseAriaLabel}
        >
          {statusBlock}
          {roomBody}
        </CommercialHostDrawer>
      </>
    );
  }

  return (
    <CommercialSectionCard {...sectionCardProps} actions={openRoomAction}>
      {statusBlock}
      {roomBody}
    </CommercialSectionCard>
  );
}
