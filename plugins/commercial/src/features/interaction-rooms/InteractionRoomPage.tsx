import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createTaskFromInteractionMessage,
  getInteractionRoom,
  listInteractionMessages,
  listInteractionRoomMembers,
  listInteractionRoomPins,
  markInteractionRoomRead,
  pinInteractionMessage,
  unpinInteractionMessage,
  type InteractionMessageDto,
  type InteractionRoomDto,
  type InteractionRoomMemberDto,
} from "../../api/interactionRoomsApi";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import {
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialMessageThread,
  CommercialPagePath,
  CommercialRoomHeader,
  CommercialStateBanner,
  CommercialStatusBadge,
} from "../../app/commercialUi";
import {
  buildInteractionRoomsPath,
  buildPluginPath,
} from "../../app/pluginRoutes";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { InteractionRoomMessageComposer } from "./InteractionRoomMessageComposer";
import { InteractionRoomMentionUnfurls } from "./InteractionRoomMentionUnfurls";
import { shouldUnfurlMentionKind } from "./entityUnfurlAdapter";
import { resolveInteractionMessageActions } from "./messageThreadTaskAction";

type Props = {
  basePath: string;
  roomId: string;
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

function kindChipLabel(room: InteractionRoomDto): string {
  if (room.kind === "process") return INTERACTION_ROOMS_CONTENT.kindProcess;
  if (room.kind === "wall") return INTERACTION_ROOMS_CONTENT.kindWall;
  if (room.entity_type) return room.entity_type;
  return INTERACTION_ROOMS_CONTENT.kindEntity;
}

/** Página da sala — só kit (header + thread + composer). */
export function InteractionRoomPage({ basePath, roomId }: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const inboxHref =
    buildInteractionRoomsPath(basePath) ?? buildPluginPath("home", basePath);

  const [room, setRoom] = useState<InteractionRoomDto | null>(null);
  const [members, setMembers] = useState<InteractionRoomMemberDto[]>([]);
  const [messages, setMessages] = useState<InteractionMessageDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [creatingTaskMessageId, setCreatingTaskMessageId] = useState<string | null>(
    null,
  );
  const [pinnedMessageIds, setPinnedMessageIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [pinningMessageId, setPinningMessageId] = useState<string | null>(null);

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
    const id = roomId.trim();
    if (!id) {
      setLoading(false);
      setError(content.roomMissingId);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void (async () => {
      try {
        const [roomData, memberRows, messageRows, pinRows] = await Promise.all([
          getInteractionRoom(id, controller.signal),
          listInteractionRoomMembers(id, controller.signal),
          listInteractionMessages(id, { limit: 50, signal: controller.signal }),
          listInteractionRoomPins(id, controller.signal),
        ]);
        if (controller.signal.aborted) return;
        setRoom(roomData);
        setMembers(memberRows);
        setMessages([...messageRows].reverse());
        setPinnedMessageIds(new Set(pinRows.map((pin) => pin.message_id)));
        void markInteractionRoomRead(id, controller.signal).catch(() => undefined);
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : content.roomLoadError);
        setRoom(null);
        setMembers([]);
        setMessages([]);
        setPinnedMessageIds(new Set());
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [roomId, content.roomMissingId, content.roomLoadError]);

  const onMessageCreated = useCallback((created: InteractionMessageDto) => {
    setMessages((prev) => [...prev, created]);
  }, []);

  const onCreateTaskFromMessage = useCallback(
    async (messageId: string) => {
      const id = roomId.trim();
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
      roomId,
      creatingTaskMessageId,
      content.createTaskOk,
      content.createTaskError,
    ],
  );

  const onTogglePin = useCallback(
    async (messageId: string, nextPinned: boolean) => {
      const id = roomId.trim();
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
    [roomId, pinningMessageId, content.pinOk, content.unpinOk, content.pinError],
  );

  const resolveActions = useCallback(
    (message: { id: string; kind: string; deleted?: boolean; bodyText: string; createdAtLabel: string }) =>
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

  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{
          label: content.inboxTitle,
          href: inboxHref,
        }}
        current={room?.title ?? content.roomFallbackTitle}
      />
      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}
      {success ? (
        <CommercialStateBanner variant="success">{success}</CommercialStateBanner>
      ) : null}
      {loading ? (
        <CommercialLoadingCard title={content.roomLoadingLabel} variant="panel" />
      ) : null}
      {!loading && room ? (
        <>
          <CommercialRoomHeader
            title={room.title}
            subtitle={
              room.entity_key
                ? `${kindChipLabel(room)} · ${room.entity_key}`
                : kindChipLabel(room)
            }
            chips={
              <CommercialStatusBadge label={kindChipLabel(room)} variant="info" />
            }
            participants={participants}
            participantsAriaLabel={content.roomMembersAriaLabel}
          />
          {threadMessages.length === 0 ? (
            <CommercialEmptyState
              title={content.roomEmptyTitle}
              message={content.roomEmptyDescription}
            />
          ) : (
            <CommercialMessageThread
              listAriaLabel={content.roomMessagesAriaLabel}
              emptyLabel={content.roomEmptyTitle}
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
      ) : null}
      {!loading && !room && !error ? (
        <CommercialEmptyState
          title={content.roomFallbackTitle}
          message={content.roomMissingId}
        />
      ) : null}
    </section>
  );
}
