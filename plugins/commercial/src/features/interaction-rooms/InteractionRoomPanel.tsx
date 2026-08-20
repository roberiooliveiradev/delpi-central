import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  createTaskFromInteractionMessage,
  deleteInteractionMessage,
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
  CommercialConversationFileDropLayer,
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
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import { useInteractionRoomSync } from "../../app/CommercialRealtimeProvider";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { useUserProfilePhotoUrls } from "../../hooks/useUserProfilePhotoUrls";
import { applyInteractionRoomRealtime } from "./applyInteractionRoomRealtime";
import type { CommercialInteractionRoomEvent } from "../../constants/interactionRoomRealtime";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { InteractionRoomMessageComposer, ROOM_ATTACH_ACCEPT } from "./InteractionRoomMessageComposer";
import { InteractionRoomMessageAttachments } from "./InteractionRoomMessageAttachments";
import { scrollThreadMessageIntoView } from "./scrollThreadMessageIntoView";
import { InteractionRoomMessageReactions } from "./InteractionRoomMessageReactions";
import { InteractionRoomMentionUnfurls } from "./InteractionRoomMentionUnfurls";
import { shouldUnfurlMentionKind } from "./entityUnfurlAdapter";
import { isOwnInteractionAuthor } from "./interactionRoomAuthor";
import {
  interactionRoomAuthorAvatarFields,
  interactionRoomParticipantAvatar,
} from "./interactionRoomUserLink";
import { resolveInteractionMessageActions } from "./messageThreadTaskAction";
import { buildEditComposerBanner, buildReplyComposerBanner } from "./interactionRoomReply";
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
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [replyMessageId, setReplyMessageId] = useState<string | null>(null);
  const [deletingMessageId, setDeletingMessageId] = useState<string | null>(null);
  const [attachmentEpochByMessageId, setAttachmentEpochByMessageId] = useState<
    Record<string, number>
  >({});
  const { currentUserId, myPortfolio } = usePortfolioScope();
  const sessionUserId = currentUserId ?? myPortfolio?.user_id ?? null;
  const confirm = useCommercialConfirm();
  const addFilesRef = useRef<(files: File[]) => void>(() => undefined);
  const msgsRef = useRef<HTMLDivElement | null>(null);
  const threadRef = useRef({
    messages,
    pinnedMessageIds,
  });
  threadRef.current = { messages, pinnedMessageIds };

  const onParentQuoteClick = useCallback((parentId: string) => {
    scrollThreadMessageIntoView(msgsRef.current, parentId);
  }, []);

  const bumpMessageAttachments = useCallback((messageId: string) => {
    const id = messageId.trim();
    if (!id) return;
    setAttachmentEpochByMessageId((prev) => ({
      ...prev,
      [id]: (prev[id] ?? 0) + 1,
    }));
  }, []);

  const onRoomRealtimeEvent = useCallback((event: CommercialInteractionRoomEvent) => {
    if (event.type === "room.attachment") {
      const messageId = (event.messageId || "").trim();
      if (messageId) bumpMessageAttachments(messageId);
      return;
    }
    const next = applyInteractionRoomRealtime(threadRef.current, event, {
      ignoreActorClientId: getCommercialClientId(),
    });
    threadRef.current = next;
    setMessages(next.messages);
    setPinnedMessageIds(next.pinnedMessageIds);
  }, [bumpMessageAttachments]);

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

  const { nameFor } = useDirectoryUserLabels(authorIds);
  const photoByUserId = useUserProfilePhotoUrls(authorIds);

  useEffect(() => {
    const key = entityKey?.trim() ?? "";
    setEditingMessageId(null);
    setReplyMessageId(null);
    setAttachmentEpochByMessageId({});
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

  const onMessageUpdated = useCallback((updated: InteractionMessageDto) => {
    setMessages((prev) =>
      prev.map((item) => (item.id === updated.id ? updated : item)),
    );
    setEditingMessageId(null);
  }, []);

  const onMessageReactionsChange = useCallback(
    (messageId: string, reactions: InteractionMessageDto["reactions"]) => {
      setMessages((prev) =>
        prev.map((item) =>
          item.id === messageId ? { ...item, reactions: reactions ?? [] } : item,
        ),
      );
    },
    [],
  );

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

  const onDeleteMessage = useCallback(
    async (messageId: string) => {
      const id = room?.id?.trim() ?? "";
      if (!id || !messageId.trim() || deletingMessageId) return;
      const ok = await confirm({
        title: content.deleteConfirmTitle,
        message: content.deleteConfirmMessage,
        confirmLabel: content.deleteConfirmLabel,
        cancelLabel: content.deleteCancelLabel,
        variant: "danger",
      });
      if (!ok) return;
      setDeletingMessageId(messageId);
      setError(null);
      setSuccess(null);
      try {
        const deleted = await deleteInteractionMessage(id, messageId);
        setMessages((prev) =>
          prev.map((item) => (item.id === deleted.id ? deleted : item)),
        );
        if (editingMessageId === messageId) setEditingMessageId(null);
        if (replyMessageId === messageId) setReplyMessageId(null);
        setSuccess(content.deleteOk);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : content.deleteError);
      } finally {
        setDeletingMessageId(null);
      }
    },
    [
      room?.id,
      deletingMessageId,
      confirm,
      content.deleteConfirmTitle,
      content.deleteConfirmMessage,
      content.deleteConfirmLabel,
      content.deleteCancelLabel,
      content.deleteOk,
      content.deleteError,
      editingMessageId,
      replyMessageId,
    ],
  );

  const resolveActions = useCallback(
    (message: {
      id: string;
      kind: string;
      deleted?: boolean;
      mine?: boolean;
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
        onEditMessage: (messageId) => {
          setReplyMessageId(null);
          setEditingMessageId(messageId);
        },
        editingMessageId,
        onReplyMessage: (messageId) => {
          setEditingMessageId(null);
          setReplyMessageId(messageId);
        },
        replyMessageId,
        onDeleteMessage: (messageId) => {
          void onDeleteMessage(messageId);
        },
        deletingMessageId,
      }),
    [
      onCreateTaskFromMessage,
      creatingTaskMessageId,
      pinnedMessageIds,
      onTogglePin,
      pinningMessageId,
      editingMessageId,
      replyMessageId,
      onDeleteMessage,
      deletingMessageId,
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
          createdAtLabel: message.edited_at
            ? `${formatMessageTime(message.created_at)} · ${content.messageEditedSuffix}`
            : formatMessageTime(message.created_at),
          authorName: message.author_user_id
            ? nameFor(message.author_user_id)
            : null,
          authorUserId: message.author_user_id,
          ...interactionRoomAuthorAvatarFields(
            message.author_user_id,
            message.author_user_id
              ? nameFor(message.author_user_id)
              : "",
            basePath,
            message.author_user_id
              ? photoByUserId.get(message.author_user_id)
              : null,
          ),
          mine: isOwnInteractionAuthor(message.author_user_id, sessionUserId),
          parentId: message.parent_id,
          deleted: Boolean(message.deleted_at),
          mentions: mentionDtos.map((mention) => ({
            kind: mention.mention_kind,
            label: mention.label,
            ref: mention.ref,
          })),
          belowBody:
            message.deleted_at != null ? null : (
              <>
                <InteractionRoomMessageReactions
                  roomId={room?.id ?? ""}
                  messageId={message.id}
                  reactions={message.reactions ?? []}
                  sessionUserId={sessionUserId}
                  onReactionsChange={onMessageReactionsChange}
                  onError={(text) => setError(text)}
                />
                <InteractionRoomMessageAttachments
                  messageId={message.id}
                  reloadToken={attachmentEpochByMessageId[message.id] ?? 0}
                />
                {hasUnfurl ? (
                  <InteractionRoomMentionUnfurls
                    basePath={basePath}
                    mentions={mentionDtos}
                  />
                ) : null}
              </>
            ),
        };
      }),
    [
      messages,
      nameFor,
      sessionUserId,
      content.messageDeleted,
      content.messageEditedSuffix,
      basePath,
      photoByUserId,
      attachmentEpochByMessageId,
      room?.id,
      onMessageReactionsChange,
    ],
  );

  const replyTarget = useMemo(() => {
    const id = (replyMessageId || "").trim();
    if (!id) return null;
    return messages.find((row) => row.id === id) ?? null;
  }, [messages, replyMessageId]);

  const replyBanner = useMemo(
    () =>
      buildReplyComposerBanner(
        replyTarget,
        replyTarget?.author_user_id
          ? nameFor(replyTarget.author_user_id)
          : null,
      ),
    [replyTarget, nameFor],
  );

  const editTarget = useMemo(() => {
    const id = (editingMessageId || "").trim();
    if (!id) return null;
    return messages.find((row) => row.id === id) ?? null;
  }, [messages, editingMessageId]);

  const editBanner = useMemo(
    () => buildEditComposerBanner(editTarget),
    [editTarget],
  );

  const participants = useMemo(
    () =>
      members.map((member) =>
        interactionRoomParticipantAvatar(
          member.user_id,
          nameFor(member.user_id),
          basePath,
          photoByUserId.get(member.user_id),
        ),
      ),
    [members, nameFor, basePath, photoByUserId],
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
      <CommercialConversationFileDropLayer
        overlayLabel={content.dropOverlayLabel}
        accept={ROOM_ATTACH_ACCEPT}
        onFiles={(files) => addFilesRef.current(files)}
      >
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
          <div className="cm-room-thread__msgs" ref={msgsRef}>
          <CommercialMessageThread
            listAriaLabel={content.roomMessagesAriaLabel}
            emptyLabel={content.panelEmptyTitle}
            messages={threadMessages}
            resolveActions={resolveActions}
            onParentQuoteClick={onParentQuoteClick}
          />
          </div>
        )}
        <InteractionRoomMessageComposer
          roomId={room.id}
          mode={editingMessageId ? "edit" : "compose"}
          editMessageId={editingMessageId}
          initialMarkdown={editTarget?.body_text ?? ""}
          initialMentions={(editTarget?.mentions ?? []).map((mention) => ({
            kind: mention.mention_kind,
            ref: { ...mention.ref },
            label: mention.label,
          }))}
          editBanner={editBanner}
          onCancelEdit={() => setEditingMessageId(null)}
          onMessageUpdated={onMessageUpdated}
          replyToMessageId={editingMessageId ? null : replyMessageId}
          replyBanner={editingMessageId ? null : replyBanner}
          onCancelReply={() => setReplyMessageId(null)}
          onMessageCreated={onMessageCreated}
          onMessageAttachmentsSettled={bumpMessageAttachments}
          onError={(message) => setError(message)}
          onAddFilesReady={(addFiles) => {
            addFilesRef.current = addFiles;
          }}
        />
      </CommercialConversationFileDropLayer>
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
