import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getInteractionRoom,
  listInteractionMessages,
  listInteractionRoomMembers,
  markInteractionRoomRead,
  postInteractionMessage,
  type InteractionMessageDto,
  type InteractionRoomDto,
  type InteractionRoomMemberDto,
} from "../../api/interactionRoomsApi";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import {
  CM_PORTAL_SCOPE,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialMentionComposer,
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
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
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
        const [roomData, memberRows, messageRows] = await Promise.all([
          getInteractionRoom(id, controller.signal),
          listInteractionRoomMembers(id, controller.signal),
          listInteractionMessages(id, { limit: 50, signal: controller.signal }),
        ]);
        if (controller.signal.aborted) return;
        setRoom(roomData);
        setMembers(memberRows);
        setMessages([...messageRows].reverse());
        void markInteractionRoomRead(id, controller.signal).catch(() => undefined);
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : content.roomLoadError);
        setRoom(null);
        setMembers([]);
        setMessages([]);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [roomId, content.roomMissingId, content.roomLoadError]);

  const onSubmit = useCallback(async () => {
    const id = roomId.trim();
    const body = draft.trim();
    if (!id || !body || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const created = await postInteractionMessage(id, { body_text: body });
      setMessages((prev) => [...prev, created]);
      setDraft("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : content.roomSendError);
    } finally {
      setSubmitting(false);
    }
  }, [roomId, draft, submitting, content.roomSendError]);

  const threadMessages = useMemo(
    () =>
      messages.map((message) => ({
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
        mentions: (message.mentions ?? []).map((mention) => ({
          kind: mention.mention_kind,
          label: mention.label,
          ref: mention.ref,
        })),
      })),
    [messages, labelFor, content.messageDeleted],
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
            />
          )}
          <CommercialMentionComposer
            value={draft}
            onChange={setDraft}
            onSubmit={() => {
              void onSubmit();
            }}
            submitting={submitting}
            portalScopeClassName={CM_PORTAL_SCOPE}
            mentionHits={[]}
            labels={{
              placeholder: content.composerPlaceholder,
              sendAriaLabel: content.composerSendAriaLabel,
              attachAriaLabel: content.composerAttachAriaLabel,
              mentionListAriaLabel: content.composerMentionListAriaLabel,
              mentionEmptyLabel: content.composerMentionEmptyLabel,
            }}
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
