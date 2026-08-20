import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { PanelRight } from "lucide-react";

import {
  createTaskFromInteractionMessage,
  deleteInteractionMessage,
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
import { getCommercialClientId } from "../../app/commercialClientId";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import { useInteractionRoomSync } from "../../app/CommercialRealtimeProvider";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { useUserProfilePhotoUrls } from "../../hooks/useUserProfilePhotoUrls";
import { applyInteractionRoomRealtime } from "./applyInteractionRoomRealtime";
import type { CommercialInteractionRoomEvent } from "../../constants/interactionRoomRealtime";
import { CommercialEntityLink } from "../../components/CommercialEntityLink";
import {
  CommercialActionButton,
  CommercialAlertQueue,
  CommercialConversationFileDropLayer,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialMessageThread,
  CommercialRoomContextPanel,
  CommercialRoomHeader,
  CommercialRoomSidePanel,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { InteractionRoomMessageComposer, ROOM_ATTACH_ACCEPT } from "./InteractionRoomMessageComposer";
import { InteractionRoomMessageAttachments } from "./InteractionRoomMessageAttachments";
import {
  InteractionRoomMessageReactionQuickBar,
  InteractionRoomMessageReactions,
} from "./InteractionRoomMessageReactions";
import { InteractionRoomMentionUnfurls } from "./InteractionRoomMentionUnfurls";
import { shouldUnfurlMentionKind } from "./entityUnfurlAdapter";
import { isOwnInteractionAuthor } from "./interactionRoomAuthor";
import {
  interactionRoomAuthorAvatarFields,
  interactionRoomParticipantAvatar,
} from "./interactionRoomUserLink";
import { resolveInteractionMessageActions } from "./messageThreadTaskAction";
import { buildEditComposerBanner, buildReplyComposerBanner } from "./interactionRoomReply";
import { resolveRoomEntityHref } from "./resolveInteractionEntityHref";
import {
  pinTitleFromMessageBody,
  scrollThreadMessageIntoView,
} from "./scrollThreadMessageIntoView";
import { shouldStickThreadToBottom } from "./threadStickToBottom";
import {
  formatInteractionMessageCreatedAtLabel,
  formatInteractionMessageTime,
} from "./interactionRoomMessageTime";

type Props = {
  basePath: string;
  roomId: string;
  variant?: "page" | "pane";
  inboxHref?: string;
  onRoomTitle?: (title: string | null) => void;
};

type RoomAlert = {
  id: string;
  title: string;
  tone: "info" | "danger";
};

/** Página da sala — só kit (header + thread + composer). */
export function InteractionRoomPage({
  basePath,
  roomId,
  variant = "page",
  onRoomTitle,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;

  const [room, setRoom] = useState<InteractionRoomDto | null>(null);
  const [members, setMembers] = useState<InteractionRoomMemberDto[]>([]);
  const [messages, setMessages] = useState<InteractionMessageDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState<RoomAlert[]>([]);
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
  const stickToBottomRef = useRef(true);
  const [contextOpen, setContextOpen] = useState(false);
  const threadRef = useRef({
    messages,
    pinnedMessageIds,
  });
  threadRef.current = { messages, pinnedMessageIds };

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

  const pushRoomAlert = useCallback((title: string, tone: RoomAlert["tone"]) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setAlerts((prev) => [...prev, { id, title, tone }]);
    window.setTimeout(() => {
      setAlerts((prev) => prev.filter((item) => item.id !== id));
    }, INTERACTION_ROOMS_CONTENT.alertDismissMs);
  }, []);

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
    const id = roomId.trim();
    setEditingMessageId(null);
    setReplyMessageId(null);
    setAttachmentEpochByMessageId({});
    if (!id) {
      setLoading(false);
      pushRoomAlert(content.roomMissingId, "danger");
      onRoomTitle?.(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
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
        onRoomTitle?.(roomData.title);
        setMembers(memberRows);
        setMessages([...messageRows].reverse());
        setPinnedMessageIds(new Set(pinRows.map((pin) => pin.message_id)));
        void markInteractionRoomRead(id, controller.signal).catch(() => undefined);
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        pushRoomAlert(
          err instanceof Error ? err.message : content.roomLoadError,
          "danger",
        );
        setRoom(null);
        onRoomTitle?.(null);
        setMembers([]);
        setMessages([]);
        setPinnedMessageIds(new Set());
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [roomId, content.roomMissingId, content.roomLoadError, onRoomTitle, pushRoomAlert]);

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
      const id = roomId.trim();
      if (!id || !messageId.trim() || creatingTaskMessageId) return;
      setCreatingTaskMessageId(messageId);
      try {
        const created = await createTaskFromInteractionMessage(id, messageId);
        setMessages((prev) => [...prev, created.task_ref_message]);
        pushRoomAlert(content.createTaskOk, "info");
      } catch (err: unknown) {
        pushRoomAlert(
          err instanceof Error ? err.message : content.createTaskError,
          "danger",
        );
      } finally {
        setCreatingTaskMessageId(null);
      }
    },
    [
      roomId,
      creatingTaskMessageId,
      content.createTaskOk,
      content.createTaskError,
      pushRoomAlert,
    ],
  );

  const onTogglePin = useCallback(
    async (messageId: string, nextPinned: boolean) => {
      const id = roomId.trim();
      if (!id || !messageId.trim() || pinningMessageId) return;
      setPinningMessageId(messageId);
      try {
        if (nextPinned) {
          await pinInteractionMessage(id, messageId);
          setPinnedMessageIds((prev) => new Set(prev).add(messageId));
          pushRoomAlert(content.pinOk, "info");
        } else {
          await unpinInteractionMessage(id, messageId);
          setPinnedMessageIds((prev) => {
            const next = new Set(prev);
            next.delete(messageId);
            return next;
          });
          pushRoomAlert(content.unpinOk, "info");
        }
      } catch (err: unknown) {
        pushRoomAlert(
          err instanceof Error ? err.message : content.pinError,
          "danger",
        );
      } finally {
        setPinningMessageId(null);
      }
    },
    [roomId, pinningMessageId, content.pinOk, content.unpinOk, content.pinError, pushRoomAlert],
  );

  const onDeleteMessage = useCallback(
    async (messageId: string) => {
      const id = roomId.trim();
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
      try {
        const deleted = await deleteInteractionMessage(id, messageId);
        setMessages((prev) =>
          prev.map((item) => (item.id === deleted.id ? deleted : item)),
        );
        if (editingMessageId === messageId) setEditingMessageId(null);
        if (replyMessageId === messageId) setReplyMessageId(null);
        pushRoomAlert(content.deleteOk, "info");
      } catch (err: unknown) {
        pushRoomAlert(
          err instanceof Error ? err.message : content.deleteError,
          "danger",
        );
      } finally {
        setDeletingMessageId(null);
      }
    },
    [
      roomId,
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
      pushRoomAlert,
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

  const resolveActionExtras = useCallback(
    (message: { id: string; deleted?: boolean }) => {
      if (message.deleted) return null;
      const row = messages.find((item) => item.id === message.id);
      if (!row) return null;
      return (
        <InteractionRoomMessageReactionQuickBar
          roomId={roomId}
          messageId={message.id}
          reactions={row.reactions ?? []}
          sessionUserId={sessionUserId}
          onReactionsChange={onMessageReactionsChange}
          onError={(text) => pushRoomAlert(text, "danger")}
        />
      );
    },
    [messages, roomId, sessionUserId, onMessageReactionsChange, pushRoomAlert],
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
          createdAtLabel: formatInteractionMessageCreatedAtLabel(
            message.created_at,
            message.edited_at,
            content.messageEditedAtTemplate,
          ),
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
                  roomId={roomId}
                  messageId={message.id}
                  reactions={message.reactions ?? []}
                  sessionUserId={sessionUserId}
                  onReactionsChange={onMessageReactionsChange}
                  onError={(text) => pushRoomAlert(text, "danger")}
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
      content.messageEditedAtTemplate,
      basePath,
      photoByUserId,
      attachmentEpochByMessageId,
      roomId,
      onMessageReactionsChange,
      pushRoomAlert,
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

  const entityHref = room
    ? resolveRoomEntityHref(basePath, room.entity_type, room.entity_key)
    : null;

  const contextPins = useMemo(
    () =>
      [...pinnedMessageIds].map((messageId) => {
        const message = messages.find((item) => item.id === messageId);
        const body =
          message?.deleted_at != null
            ? content.messageDeleted
            : message?.body_text;
        return {
          id: messageId,
          messageId,
          title: pinTitleFromMessageBody(body, content.roomFallbackTitle),
          dateLabel: formatInteractionMessageTime(message?.created_at),
        };
      }),
    [
      pinnedMessageIds,
      messages,
      content.messageDeleted,
      content.roomFallbackTitle,
    ],
  );

  const onSelectPin = useCallback((messageId: string) => {
    stickToBottomRef.current = false;
    scrollThreadMessageIntoView(msgsRef.current, messageId);
  }, []);

  const onParentQuoteClick = useCallback((parentId: string) => {
    stickToBottomRef.current = false;
    scrollThreadMessageIntoView(msgsRef.current, parentId);
  }, []);

  useEffect(() => {
    const el = msgsRef.current;
    if (!el || !stickToBottomRef.current) return;
    el.scrollTop = el.scrollHeight;
  }, [threadMessages.length, loading]);

  return (
    <section className={variant === "page" ? "cm-page-stack cm-room-thread" : "cm-room-thread"}>
      {alerts.length > 0 ? (
        <div className="cm-room-alert-host">
          <CommercialAlertQueue
            items={alerts}
            aria-label={content.roomAlertsAriaLabel}
          />
        </div>
      ) : null}
      {loading ? (
        <CommercialLoadingCard title={content.roomLoadingLabel} variant="panel" />
      ) : null}
      {!loading && room ? (
        <CommercialConversationFileDropLayer
          overlayLabel={content.dropOverlayLabel}
          accept={ROOM_ATTACH_ACCEPT}
          onFiles={(files) => addFilesRef.current(files)}
        >
          <div className="cm-room-thread__header">
            <CommercialRoomHeader
              title={room.title}
              subtitle={
                room.entity_key ? (
                  entityHref ? (
                    <CommercialEntityLink
                      href={entityHref}
                      title={content.contextOpenEntity}
                    >
                      {room.entity_key}
                    </CommercialEntityLink>
                  ) : (
                    room.entity_key
                  )
                ) : undefined
              }
              participants={participants}
              participantsAriaLabel={content.roomMembersAriaLabel}
              actions={
                <CommercialActionButton
                  variant="ghost"
                  aria-label={content.contextToggle}
                  aria-expanded={contextOpen}
                  onClick={() => setContextOpen((open) => !open)}
                >
                  <PanelRight size={16} aria-hidden />
                </CommercialActionButton>
              }
            />
          </div>
          <div className="cm-room-thread__body">
            <div className="cm-room-thread__main">
              <div className="cm-room-thread__stage">
                <div
                  className="cm-room-thread__msgs"
                  ref={msgsRef}
                  onScroll={(event) => {
                    stickToBottomRef.current = shouldStickThreadToBottom(
                      event.currentTarget,
                    );
                  }}
                >
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
                    resolveActionExtras={resolveActionExtras}
                    onParentQuoteClick={onParentQuoteClick}
                  />
                )}
                </div>
              </div>
              <div className="cm-room-thread__dock">
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
                  onError={(message) => pushRoomAlert(message, "danger")}
                  onAddFilesReady={(addFiles) => {
                    addFilesRef.current = addFiles;
                  }}
                />
              </div>
            </div>
            <CommercialRoomSidePanel open={contextOpen} title={content.contextToggle}>
              <CommercialRoomContextPanel
                embedded
                flush
                labels={{
                  about: content.contextAbout,
                  participants: content.contextParticipants,
                  pins: content.contextPins,
                  pinsEmpty: content.contextPinsEmpty,
                  membersEmpty: content.contextMembersEmpty,
                  openEntity: content.contextOpenEntity,
                }}
                entityTitle={room.title}
                entityKey={room.entity_key}
                entityHref={entityHref}
                onOpenEntity={
                  entityHref
                    ? () => {
                        navigatePluginPath(entityHref);
                      }
                    : undefined
                }
                participants={participants}
                participantsAriaLabel={content.roomMembersAriaLabel}
                pins={contextPins}
                onPinSelect={onSelectPin}
              />
            </CommercialRoomSidePanel>
          </div>
        </CommercialConversationFileDropLayer>
      ) : null}
      {!loading && !room ? (
        <CommercialEmptyState
          title={content.roomFallbackTitle}
          message={content.roomMissingId}
        />
      ) : null}
    </section>
  );
}
