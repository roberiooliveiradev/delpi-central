import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  createTaskFromInteractionMessage,
  listInteractionMessages,
  listInteractionRoomMembers,
  listInteractionRoomPins,
  markInteractionRoomRead,
  pinInteractionMessage,
  resolveInteractionRoom,
  unpinInteractionMessage,
  type InteractionMessageDto,
  type InteractionRoomDto,
  type InteractionRoomMemberDto,
} from "../../api/interactionRoomsApi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialHostDrawer,
  CommercialLoadingCard,
  CommercialMessageThread,
  CommercialRoomHeader,
  CommercialSectionCard,
  CommercialStateBanner,
} from "../../app/commercialUi";
import { buildInteractionRoomPath } from "../../app/pluginRoutes";
import { getCommercialClientId } from "../../app/commercialClientId";
import { useInteractionRoomSync } from "../../app/CommercialRealtimeProvider";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { applyInteractionRoomRealtime } from "./applyInteractionRoomRealtime";
import type { CommercialInteractionRoomEvent } from "../../constants/interactionRoomRealtime";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { InteractionRoomMessageComposer } from "./InteractionRoomMessageComposer";
import { InteractionRoomMentionUnfurls } from "./InteractionRoomMentionUnfurls";
import { shouldUnfurlMentionKind } from "./entityUnfurlAdapter";
import { resolveInteractionMessageActions } from "./messageThreadTaskAction";
import {
  INTERACTION_ROOM_NARROW_QUERY,
  useMatchMedia,
} from "./useMatchMedia";

const EMBED_MESSAGE_LIMIT = 30;

type Props = {
  basePath: string;
  entityType: string;
  entityKey: string | null;
  roomTitle: string;
};

function formatMessageTime(iso: string | null | undefined): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Painel embutido na ficha — resolve lazy + thread/composer do kit.
 * Viewport ≤768px: conversa no drawer host-contained (não cobre a sidebar).
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
  const [members, setMembers] = useState<InteractionRoomMemberDto[]>([]);
  const [messages, setMessages] = useState<InteractionMessageDto[]>([]);
  const [loading, setLoading] = useState(Boolean(entityKey));
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [creatingTaskMessageId, setCreatingTaskMessageId] = useState<string | null>(
    null,
  );
  const [pinnedMessageIds, setPinnedMessageIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [pinningMessageId, setPinningMessageId] = useState<string | null>(null);
  const threadRef = useRef({
    messages,
    pinnedMessageIds,
  });
  threadRef.current = { messages, pinnedMessageIds };

  const onRoomRealtimeEvent = useCallback((event: CommercialInteractionRoomEvent) => {
    const next = applyInteractionRoomRealtime(threadRef.current, event, {
      ignoreActorClientId: getCommercialClientId(),
    });
    threadRef.current = next;
    setMessages(next.messages);
    setPinnedMessageIds(next.pinnedMessageIds);
  }, []);

  useInteractionRoomSync(room?.id, onRoomRealtimeEvent, Boolean(room?.id));

  const authorIds = useMemo(() => {
    const ids = new Set<string>();
    for (const member of members) {
      if (member.user_id) ids.add(member.user_id);
    }
    for (const message of messages) {
      if (message.author_user_id) ids.add(message.author_user_id);
    }
    return [...ids];
  }, [members, messages]);

  const { labelFor } = useDirectoryUserLabels(authorIds);

  useEffect(() => {
    const key = entityKey?.trim() ?? "";
    if (!key) {
      setLoading(false);
      setRoom(null);
      setMembers([]);
      setMessages([]);
      setPinnedMessageIds(new Set());
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
        const [memberRows, messageRows, pinRows] = await Promise.all([
          listInteractionRoomMembers(resolved.id, controller.signal),
          listInteractionMessages(resolved.id, {
            limit: EMBED_MESSAGE_LIMIT,
            signal: controller.signal,
          }),
          listInteractionRoomPins(resolved.id, controller.signal),
        ]);
        if (controller.signal.aborted) return;
        setRoom(resolved);
        setMembers(memberRows);
        setMessages([...messageRows].reverse());
        setPinnedMessageIds(new Set(pinRows.map((pin) => pin.message_id)));
        void markInteractionRoomRead(resolved.id, controller.signal).catch(
          () => undefined,
        );
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof Error ? err.message : content.panelResolveError,
        );
        setRoom(null);
        setMembers([]);
        setMessages([]);
        setPinnedMessageIds(new Set());
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [entityType, entityKey, roomTitle, content.panelResolveError]);

  useEffect(() => {
    if (!narrow) setDrawerOpen(false);
  }, [narrow]);

  const onMessageCreated = useCallback((created: InteractionMessageDto) => {
    setMessages((prev) => [...prev, created]);
  }, []);

  const onCreateTaskFromMessage = useCallback(
    async (messageId: string) => {
      const id = room?.id?.trim() ?? "";
      if (!id || !messageId.trim() || creatingTaskMessageId) return;
      setCreatingTaskMessageId(messageId);
      setError(null);
      setSuccess(null);
      try {
        const created = await createTaskFromInteractionMessage(id, messageId);
        setMessages((prev) => [...prev, created.task_ref_message]);
        setSuccess(content.createTaskOk);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : content.createTaskError);
      } finally {
        setCreatingTaskMessageId(null);
      }
    },
    [
      room?.id,
      creatingTaskMessageId,
      content.createTaskOk,
      content.createTaskError,
    ],
  );

  const onTogglePin = useCallback(
    async (messageId: string, nextPinned: boolean) => {
      const id = room?.id?.trim() ?? "";
      if (!id || !messageId.trim() || pinningMessageId) return;
      setPinningMessageId(messageId);
      setError(null);
      setSuccess(null);
      try {
        if (nextPinned) {
          await pinInteractionMessage(id, messageId);
          setPinnedMessageIds((prev) => new Set(prev).add(messageId));
          setSuccess(content.pinOk);
        } else {
          await unpinInteractionMessage(id, messageId);
          setPinnedMessageIds((prev) => {
            const next = new Set(prev);
            next.delete(messageId);
            return next;
          });
          setSuccess(content.unpinOk);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : content.pinError);
      } finally {
        setPinningMessageId(null);
      }
    },
    [
      room?.id,
      pinningMessageId,
      content.pinOk,
      content.unpinOk,
      content.pinError,
    ],
  );

  const resolveActions = useCallback(
    (message: {
      id: string;
      kind: string;
      deleted?: boolean;
      bodyText: string;
      createdAtLabel: string;
    }) =>
      resolveInteractionMessageActions({
        message,
        onCreateTask: (messageId) => {
          void onCreateTaskFromMessage(messageId);
        },
        creatingMessageId: creatingTaskMessageId,
        pinnedMessageIds,
        onTogglePin: (messageId, nextPinned) => {
          void onTogglePin(messageId, nextPinned);
        },
        pinningMessageId,
      }),
    [
      onCreateTaskFromMessage,
      creatingTaskMessageId,
      pinnedMessageIds,
      onTogglePin,
      pinningMessageId,
    ],
  );

  const threadMessages = useMemo(
    () =>
      messages.map((message) => {
        const mentionDtos = message.mentions ?? [];
        const hasUnfurl = mentionDtos.some((mention) =>
          shouldUnfurlMentionKind(mention.mention_kind),
        );
        return {
          id: message.id,
          kind: message.message_kind,
          bodyText:
            message.deleted_at != null
              ? content.messageDeleted
              : message.body_text,
          createdAtLabel: formatMessageTime(message.created_at),
          authorName: message.author_user_id
            ? labelFor(message.author_user_id)
            : null,
          authorUserId: message.author_user_id,
          parentId: message.parent_id,
          deleted: Boolean(message.deleted_at),
          mentions: mentionDtos.map((mention) => ({
            kind: mention.mention_kind,
            label: mention.label,
            ref: mention.ref,
          })),
          belowBody: hasUnfurl ? (
            <InteractionRoomMentionUnfurls
              basePath={basePath}
              mentions={mentionDtos}
            />
          ) : null,
        };
      }),
    [messages, labelFor, content.messageDeleted, basePath],
  );

  const participants = useMemo(
    () =>
      members.map((member) => ({
        id: member.user_id,
        name: labelFor(member.user_id),
      })),
    [members, labelFor],
  );

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
    !loading && room ? (
      <>
        <CommercialRoomHeader
          title={room.title || roomTitle}
          participants={participants}
          participantsAriaLabel={content.roomMembersAriaLabel}
        />
        {threadMessages.length === 0 ? (
          <CommercialEmptyState
            title={content.panelEmptyTitle}
            message={content.panelEmptyDescription}
          />
        ) : (
          <CommercialMessageThread
            listAriaLabel={content.roomMessagesAriaLabel}
            emptyLabel={content.panelEmptyTitle}
            messages={threadMessages}
            resolveActions={resolveActions}
          />
        )}
        <InteractionRoomMessageComposer
          roomId={room.id}
          onMessageCreated={onMessageCreated}
          onError={(message) => setError(message)}
        />
      </>
    ) : null;

  const statusBlock = (
    <>
      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}
      {success ? (
        <CommercialStateBanner variant="success">{success}</CommercialStateBanner>
      ) : null}
      {loading ? (
        <CommercialLoadingCard title={content.panelLoadingLabel} variant="panel" />
      ) : null}
    </>
  );

  if (!entityKey?.trim()) {
    return (
      <CommercialSectionCard title={content.panelTitle}>
        <CommercialStateBanner variant="warning">
          {content.panelMissingKey}
        </CommercialStateBanner>
      </CommercialSectionCard>
    );
  }

  if (narrow) {
    return (
      <>
        <CommercialSectionCard title={content.panelTitle} actions={openRoomAction}>
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
    <CommercialSectionCard title={content.panelTitle} actions={openRoomAction}>
      {statusBlock}
      {roomBody}
    </CommercialSectionCard>
  );
}
