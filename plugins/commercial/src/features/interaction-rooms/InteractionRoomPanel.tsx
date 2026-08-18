import { useCallback, useEffect, useMemo, useState } from "react";

import {
  listInteractionMessages,
  listInteractionRoomMembers,
  markInteractionRoomRead,
  resolveInteractionRoom,
  type InteractionMessageDto,
  type InteractionRoomDto,
  type InteractionRoomMemberDto,
} from "../../api/interactionRoomsApi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialMessageThread,
  CommercialRoomHeader,
  CommercialSectionCard,
  CommercialStateBanner,
} from "../../app/commercialUi";
import { buildInteractionRoomPath } from "../../app/pluginRoutes";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { InteractionRoomMessageComposer } from "./InteractionRoomMessageComposer";
import { InteractionRoomMentionUnfurls } from "./InteractionRoomMentionUnfurls";
import { shouldUnfurlMentionKind } from "./entityUnfurlAdapter";

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
 * Painel embutido na ficha — resolve lazy + thread/composer do kit (sem chrome local).
 */
export function InteractionRoomPanel({
  basePath,
  entityType,
  entityKey,
  roomTitle,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [room, setRoom] = useState<InteractionRoomDto | null>(null);
  const [members, setMembers] = useState<InteractionRoomMemberDto[]>([]);
  const [messages, setMessages] = useState<InteractionMessageDto[]>([]);
  const [loading, setLoading] = useState(Boolean(entityKey));
  const [error, setError] = useState<string | null>(null);

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
        const [memberRows, messageRows] = await Promise.all([
          listInteractionRoomMembers(resolved.id, controller.signal),
          listInteractionMessages(resolved.id, {
            limit: EMBED_MESSAGE_LIMIT,
            signal: controller.signal,
          }),
        ]);
        if (controller.signal.aborted) return;
        setRoom(resolved);
        setMembers(memberRows);
        setMessages([...messageRows].reverse());
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
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [entityType, entityKey, roomTitle, content.panelResolveError]);

  const onMessageCreated = useCallback((created: InteractionMessageDto) => {
    setMessages((prev) => [...prev, created]);
  }, []);

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

  if (!entityKey?.trim()) {
    return (
      <CommercialSectionCard title={content.panelTitle}>
        <CommercialStateBanner variant="warning">
          {content.panelMissingKey}
        </CommercialStateBanner>
      </CommercialSectionCard>
    );
  }

  return (
    <CommercialSectionCard title={content.panelTitle} actions={openRoomAction}>
      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}
      {loading ? (
        <CommercialLoadingCard title={content.panelLoadingLabel} variant="panel" />
      ) : null}
      {!loading && room ? (
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
            />
          )}
          <InteractionRoomMessageComposer
            roomId={room.id}
            onMessageCreated={onMessageCreated}
            onError={(message) => setError(message)}
          />
        </>
      ) : null}
    </CommercialSectionCard>
  );
}
