import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  INTERACTION_ROOM_PAGE_LABELS_PT,
  InteractionRoomPage as KitInteractionRoomPage,
  roomHeaderBemClasses,
  type InteractionRoomMessage,
  type InteractionRoomPageLabels,
  type InteractionRoomSharedItem,
} from "@delpi/plugin-ui/index";

import {
  createTaskFromInteractionMessage,
  deleteInteractionMessage,
  deleteInteractionRoom,
  downloadRoomMessageAttachmentBlob,
  renameInteractionRoom,
  getInteractionRoom,
  listInteractionMessages,
  listInteractionRoomMembers,
  listInteractionRoomPins,
  listRoomSharedItems,
  markInteractionRoomRead,
  pinInteractionMessage,
  unpinInteractionMessage,
  type InteractionMessageDto,
  type InteractionRoomDto,
  type InteractionRoomMemberDto,
  type InteractionRoomSharedItemDto,
} from "../../api/interactionRoomsApi";
import { getCommercialClientId } from "../../app/commercialClientId";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { useInteractionRoomSync } from "../../app/CommercialRealtimeProvider";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { useUserProfilePhotoUrls } from "../../hooks/useUserProfilePhotoUrls";
import { applyInteractionRoomRealtime } from "./applyInteractionRoomRealtime";
import { resolveThreadLoadingState } from "./interactionRoomLoadingState";
import {
  formatInteractionRoomPinByOtherNotice,
  formatInteractionRoomReactionByOtherNotice,
  interactionRoomNoticeVariantForComposerKind,
  isInteractionRoomOwnActor,
  type InteractionRoomComposerNoticeKind,
} from "./interactionRoomNoticePolicy";
import type { CommercialInteractionRoomEvent } from "../../constants/interactionRoomRealtime";
import {
  CM_PORTAL_SCOPE,
  CommercialEmptyState,
  CommercialLoadingCard,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { buildInteractionRoomsPath } from "../../app/pluginRoutes";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { formatRoomEntityPresentation } from "./interactionRoomEntityPresentation";
import { InteractionRoomMessageComposer, ROOM_ATTACH_ACCEPT } from "./InteractionRoomMessageComposer";
import { InteractionRoomMoreMenu } from "./InteractionRoomMoreMenu";
import { InteractionRoomRenameDialog } from "./InteractionRoomRenameDialog";
import { InteractionRoomMessageAttachments } from "./InteractionRoomMessageAttachments";
import { listInlineAttachmentIdsFromMarkdown } from "./interactionRoomInlineAttachments";
import {
  TaskAttachmentPreviewModal,
  type TaskAttachmentPreviewTarget,
} from "../my-day/TaskAttachmentPreviewModal";
import type { CommercialAttachmentDto } from "../../api/attachmentsApi";
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
import { buildCreateTaskMessageAction } from "./messageThreadTaskAction";
import { buildEditComposerBanner, buildReplyComposerBanner } from "./interactionRoomReply";
import { mapInteractionMentionsToTextItems } from "./mapInteractionMentionToTextItem";
import { resolveRoomEntityHref } from "./resolveInteractionEntityHref";
import { formatInteractionMessageCreatedAtLabel, formatInteractionMessageTime } from "./interactionRoomMessageTime";

type Props = {
  basePath: string;
  roomId: string;
  variant?: "page" | "pane";
  inboxHref?: string;
  onRoomTitle?: (title: string | null) => void;
};

const noopInboxQueryChange = () => undefined;
const noopDraftChange = () => undefined;
const noopSubmit = () => undefined;

/** Host da sala Commercial — domínio no MFE; chrome canônico via kit InteractionRoomPage. */
export function CommercialInteractionRoomHost({
  basePath,
  roomId,
  variant = "page",
  inboxHref,
  onRoomTitle,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const roomHeaderClasses = useMemo(() => roomHeaderBemClasses("cm"), []);

  const pageLabels = useMemo<InteractionRoomPageLabels>(
    () => ({
      ...INTERACTION_ROOM_PAGE_LABELS_PT,
      backAriaLabel: content.inboxBackAriaLabel,
      emptyThreadTitle: content.roomEmptyTitle,
      emptyThreadMessage: content.roomEmptyDescription,
      loadingThreadTitle: content.roomLoadingLabel,
      messagesAriaLabel: content.roomMessagesAriaLabel,
      dropOverlay: content.dropOverlayLabel,
      roomViewChat: content.roomViewChat,
      roomViewShared: content.roomViewShared,
      roomViewNavAriaLabel: content.roomViewNavAriaLabel,
      findAriaLabel: content.findInChatAriaLabel,
      contextAriaLabel: content.contextToggle,
      contextCloseAriaLabel: content.contextToggleCloseAriaLabel,
      contextTitle: content.contextToggle,
      sharedRecent: content.sharedKindRecent,
      sharedFiles: content.sharedKindFiles,
      sharedLinks: content.sharedKindLinks,
      sharedFilterPlaceholder: content.sharedFilterPlaceholder,
      sharedEmptyTitle: content.sharedEmptyTitle,
      sharedEmptyMessage: content.sharedEmptyDescription,
      sharedListAriaLabel: content.roomViewShared,
      pin: content.pinActionLabel,
      unpin: content.unpinActionLabel,
      edit: content.editActionLabel,
      delete: content.deleteActionLabel,
      reply: content.replyActionLabel,
      actionsToolbarAriaLabel: content.messageActionsToolbarAriaLabel,
      find: {
        title: content.findInChatTitle,
        closeAriaLabel: content.findInChatCloseAriaLabel,
        placeholder: content.findInChatPlaceholder,
        clear: content.findInChatClear,
        empty: content.findInChatEmpty,
        loading: content.findInChatLoading,
      },
      context: {
        about: content.contextAbout,
        participants: content.contextParticipants,
        pins: content.contextPins,
        pinsEmpty: content.contextPinsEmpty,
        membersEmpty: content.contextMembersEmpty,
        openEntity: content.contextOpenEntity,
      },
    }),
    [content],
  );

  const [room, setRoom] = useState<InteractionRoomDto | null>(null);
  const [members, setMembers] = useState<InteractionRoomMemberDto[]>([]);
  const [messages, setMessages] = useState<InteractionMessageDto[]>([]);
  const [loading, setLoading] = useState(true);
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
  const [deletingRoomId, setDeletingRoomId] = useState<string | null>(null);
  const [attachmentEpochByMessageId, setAttachmentEpochByMessageId] = useState<
    Record<string, number>
  >({});
  const [attachmentThumbUrls, setAttachmentThumbUrls] = useState<Record<string, string>>(
    {},
  );
  const [inlinePreview, setInlinePreview] = useState<TaskAttachmentPreviewTarget>(null);
  const [sharedRows, setSharedRows] = useState<InteractionRoomSharedItemDto[]>([]);
  const attachmentMetaRef = useRef<Record<string, CommercialAttachmentDto>>({});
  const sharedRowsRef = useRef<InteractionRoomSharedItemDto[]>([]);
  sharedRowsRef.current = sharedRows;
  const { currentUserId, myPortfolio, canManagePortfolios } = usePortfolioScope();
  const sessionUserId = currentUserId ?? myPortfolio?.user_id ?? null;
  const confirm = useCommercialConfirm();
  const { notifySuccess, notifyError, notifyInfo } = useCommercialFloatingNotice();
  const addFilesRef = useRef<(files: File[]) => void>(() => undefined);
  const roomSnapshotRef = useRef<{ roomId: string; hasData: boolean }>({
    roomId: "",
    hasData: false,
  });
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [renamingRoom, setRenamingRoom] = useState(false);
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

  const mergeAttachmentThumbUrls = useCallback((urls: Record<string, string>) => {
    setAttachmentThumbUrls((prev) => {
      let changed = false;
      const next = { ...prev };
      for (const [id, url] of Object.entries(urls)) {
        if (!url) {
          if (id in next) {
            delete next[id];
            changed = true;
          }
        } else if (next[id] !== url) {
          next[id] = url;
          changed = true;
        }
      }
      return changed ? next : prev;
    });
  }, []);

  const reloadSharedItems = useCallback(
    async (id: string, signal?: AbortSignal) => {
      try {
        const rows = await listRoomSharedItems(id, {
          kind: "all",
          signal,
        });
        if (signal?.aborted) return;
        setSharedRows(rows);
      } catch {
        if (signal?.aborted) return;
        setSharedRows([]);
      }
    },
    [],
  );

  const onRoomRealtimeEvent = useCallback((event: CommercialInteractionRoomEvent) => {
    const selfClientId = getCommercialClientId();
    if (event.type === "room.deleted") {
      if (isInteractionRoomOwnActor(event.actorClientId, selfClientId)) return;
      setRoom(null);
      onRoomTitle?.(null);
      setMembers([]);
      setMessages([]);
      setPinnedMessageIds(new Set());
      setSharedRows([]);
      notifyError(content.deleteRoomDeletedElsewhere);
      const href = buildInteractionRoomsPath(basePath);
      if (href) navigatePluginPath(href);
      return;
    }
    if (event.type === "room.updated") {
      const title = (event.title || "").trim();
      if (title) {
        setRoom((prev) => (prev ? { ...prev, title } : prev));
        onRoomTitle?.(title);
      }
      return;
    }
    if (
      event.type === "room.pin" &&
      !isInteractionRoomOwnActor(event.actorClientId, selfClientId)
    ) {
      notifyInfo(
        formatInteractionRoomPinByOtherNotice(event.actorDisplayName || ""),
      );
    }
    if (
      event.type === "room.reaction" &&
      !isInteractionRoomOwnActor(event.actorClientId, selfClientId)
    ) {
      notifyInfo(
        formatInteractionRoomReactionByOtherNotice(
          event.actorDisplayName || "",
          event.code || "",
        ),
      );
    }
    if (event.type === "room.attachment") {
      const messageId = (event.messageId || "").trim();
      if (messageId) bumpMessageAttachments(messageId);
      const id = roomId.trim();
      if (id) void reloadSharedItems(id);
      return;
    }
    const next = applyInteractionRoomRealtime(threadRef.current, event, {
      ignoreActorClientId: selfClientId,
    });
    threadRef.current = next;
    setMessages(next.messages);
    setPinnedMessageIds(next.pinnedMessageIds);
  }, [
    bumpMessageAttachments,
    basePath,
    onRoomTitle,
    notifyError,
    notifyInfo,
    content.deleteRoomDeletedElsewhere,
    roomId,
    reloadSharedItems,
  ]);

  const pushRoomNotice = useCallback(
    (message: string, kind: InteractionRoomComposerNoticeKind) => {
      const variant = interactionRoomNoticeVariantForComposerKind(kind);
      if (variant === "error") notifyError(message);
      else if (variant === "info") notifyInfo(message);
      else if (variant === "warning") notifyInfo(message, { autoDismissMs: 6500 });
      else notifySuccess(message);
    },
    [notifyError, notifyInfo, notifySuccess],
  );

  useInteractionRoomSync(room?.id, onRoomRealtimeEvent, Boolean(room?.id));

  const authorIds = useMemo(() => {
    const ids = new Set<string>();
    for (const member of members) {
      if (member.user_id) ids.add(member.user_id);
    }
    for (const message of messages) {
      if (message.author_user_id) ids.add(message.author_user_id);
    }
    for (const item of sharedRows) {
      const sharedBy = (item.shared_by || "").trim();
      if (sharedBy) ids.add(sharedBy);
    }
    return [...ids];
  }, [members, messages, sharedRows]);

  const { nameFor } = useDirectoryUserLabels(authorIds);
  const photoByUserId = useUserProfilePhotoUrls(authorIds);

  useEffect(() => {
    const id = roomId.trim();
    setEditingMessageId(null);
    setReplyMessageId(null);
    setAttachmentEpochByMessageId({});
    if (!id) {
      setLoading(false);
      pushRoomNotice(content.roomMissingId, "error");
      onRoomTitle?.(null);
      return;
    }
    const controller = new AbortController();
    const keepSnapshot =
      roomSnapshotRef.current.roomId === id &&
      id !== "" &&
      roomSnapshotRef.current.hasData;
    if (!keepSnapshot) {
      setRoom(null);
      onRoomTitle?.(null);
      setMembers([]);
      setMessages([]);
      setPinnedMessageIds(new Set());
      setSharedRows([]);
      roomSnapshotRef.current = { roomId: id, hasData: false };
    }
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
        roomSnapshotRef.current = { roomId: id, hasData: true };
        void markInteractionRoomRead(id, controller.signal).catch(() => undefined);
        void reloadSharedItems(id, controller.signal);
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        pushRoomNotice(
          err instanceof Error ? err.message : content.roomLoadError,
          "error",
        );
        setRoom(null);
        onRoomTitle?.(null);
        setMembers([]);
        setMessages([]);
        setPinnedMessageIds(new Set());
        setSharedRows([]);
        roomSnapshotRef.current = { roomId: id, hasData: false };
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [
    roomId,
    content.roomMissingId,
    content.roomLoadError,
    onRoomTitle,
    pushRoomNotice,
    reloadSharedItems,
  ]);

  const onMessageCreated = useCallback(
    (created: InteractionMessageDto) => {
      setMessages((prev) => [...prev, created]);
      const id = roomId.trim();
      if (id) void reloadSharedItems(id);
    },
    [reloadSharedItems, roomId],
  );

  const onMessageUpdated = useCallback(
    (updated: InteractionMessageDto) => {
      setMessages((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      );
      setEditingMessageId(null);
      const id = roomId.trim();
      if (id) void reloadSharedItems(id);
    },
    [reloadSharedItems, roomId],
  );

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
        pushRoomNotice(content.createTaskOk, "info");
      } catch (err: unknown) {
        pushRoomNotice(
          err instanceof Error ? err.message : content.createTaskError,
          "error",
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
      pushRoomNotice,
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
          pushRoomNotice(content.pinOk, "info");
        } else {
          await unpinInteractionMessage(id, messageId);
          setPinnedMessageIds((prev) => {
            const next = new Set(prev);
            next.delete(messageId);
            return next;
          });
          pushRoomNotice(content.unpinOk, "info");
        }
      } catch (err: unknown) {
        pushRoomNotice(
          err instanceof Error ? err.message : content.pinError,
          "error",
        );
      } finally {
        setPinningMessageId(null);
      }
    },
    [roomId, pinningMessageId, content.pinOk, content.unpinOk, content.pinError, pushRoomNotice],
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
        pushRoomNotice(content.deleteOk, "info");
        void reloadSharedItems(id);
      } catch (err: unknown) {
        pushRoomNotice(
          err instanceof Error ? err.message : content.deleteError,
          "error",
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
      pushRoomNotice,
      reloadSharedItems,
    ],
  );

  const onDeleteRoom = useCallback(async () => {
    const id = roomId.trim();
    if (!canManagePortfolios || !id || deletingRoomId) return;
    const ok = await confirm({
      title: content.deleteRoomConfirmTitle,
      message: content.deleteRoomConfirmMessage,
      confirmLabel: content.deleteRoomConfirmLabel,
      cancelLabel: content.deleteRoomCancelLabel,
      variant: "danger",
    });
    if (!ok) return;
    setDeletingRoomId(id);
    try {
      await deleteInteractionRoom(id);
      notifySuccess(content.deleteRoomOk);
      setRoom(null);
      onRoomTitle?.(null);
      const href = buildInteractionRoomsPath(basePath);
      if (href) navigatePluginPath(href);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : content.deleteRoomError);
    } finally {
      setDeletingRoomId(null);
    }
  }, [
    roomId,
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
    onRoomTitle,
    basePath,
  ]);

  const onRenameRoomSave = useCallback(
    async (nextTitle: string) => {
      const id = roomId.trim();
      const title = nextTitle.trim();
      if (!id || !title || renamingRoom) return;
      if (title === (room?.title ?? "").trim()) {
        setRenameDialogOpen(false);
        return;
      }
      setRenamingRoom(true);
      try {
        const updated = await renameInteractionRoom(id, title);
        setRoom((prev) =>
          prev && prev.id === updated.id
            ? { ...prev, title: updated.title, updated_at: updated.updated_at }
            : prev,
        );
        onRoomTitle?.(updated.title);
        notifySuccess(content.renameRoomOk);
        setRenameDialogOpen(false);
      } catch (err: unknown) {
        notifyError(
          err instanceof Error ? err.message : content.renameRoomError,
        );
      } finally {
        setRenamingRoom(false);
      }
    },
    [
      roomId,
      room?.title,
      renamingRoom,
      notifySuccess,
      notifyError,
      onRoomTitle,
      content.renameRoomOk,
      content.renameRoomError,
    ],
  );

  const resolveExtraActions = useCallback(
    (message: InteractionRoomMessage) => {
      const action = buildCreateTaskMessageAction({
        message,
        onCreateTask: (messageId) => {
          void onCreateTaskFromMessage(messageId);
        },
        busy:
          creatingTaskMessageId === message.id ||
          pinningMessageId === message.id ||
          deletingMessageId === message.id,
      });
      return action ? [action] : [];
    },
    [
      onCreateTaskFromMessage,
      creatingTaskMessageId,
      pinningMessageId,
      deletingMessageId,
    ],
  );

  const resolveActionExtras = useCallback(
    (message: InteractionRoomMessage) => {
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
          onError={(text) => pushRoomNotice(text, "error")}
        />
      );
    },
    [messages, roomId, sessionUserId, onMessageReactionsChange, pushRoomNotice],
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
          pinned: pinnedMessageIds.has(message.id),
          mentions: mapInteractionMentionsToTextItems(mentionDtos, {
            basePath,
            photoByUserId,
          }),
          belowBody:
            message.deleted_at != null ? null : (
              <>
                <InteractionRoomMessageReactions
                  roomId={roomId}
                  messageId={message.id}
                  reactions={message.reactions ?? []}
                  sessionUserId={sessionUserId}
                  onReactionsChange={onMessageReactionsChange}
                  onError={(text) => pushRoomNotice(text, "error")}
                />
                <InteractionRoomMessageAttachments
                  messageId={message.id}
                  reloadToken={attachmentEpochByMessageId[message.id] ?? 0}
                  excludeAttachmentIds={listInlineAttachmentIdsFromMarkdown(
                    message.body_text,
                  )}
                  onThumbUrlsChange={mergeAttachmentThumbUrls}
                  onItemsChange={(items) => {
                    for (const item of items) {
                      attachmentMetaRef.current[item.id] = item;
                    }
                  }}
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
      pinnedMessageIds,
      onMessageReactionsChange,
      pushRoomNotice,
      mergeAttachmentThumbUrls,
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

  const entityPresentation = useMemo(
    () =>
      formatRoomEntityPresentation(room?.entity_type, room?.entity_key, room?.title),
    [room?.entity_key, room?.entity_type, room?.title],
  );

  const sharedItems = useMemo<InteractionRoomSharedItem[]>(
    () =>
      sharedRows.map((item) => {
        const sharedBy = (item.shared_by || "").trim();
        const kind = item.kind === "link" ? "link" : "file";
        return {
          id: item.id,
          kind,
          title: item.title,
          subtitle: item.subtitle,
          whenLabel: formatInteractionMessageTime(item.shared_at),
          whoLabel: sharedBy ? nameFor(sharedBy) : null,
          href: item.href,
          ariaLabel:
            kind === "link"
              ? content.sharedOpenLinkAriaLabel
              : content.sharedOpenFileAriaLabel.replace(
                  "{fileName}",
                  item.title || "file",
                ),
        };
      }),
    [
      sharedRows,
      nameFor,
      content.sharedOpenFileAriaLabel,
      content.sharedOpenLinkAriaLabel,
    ],
  );

  const onOpenShared = useCallback(
    (item: InteractionRoomSharedItem) => {
      const source = sharedRowsRef.current.find((row) => row.id === item.id);
      if (!source) return;
      if (source.kind === "link" && source.href) {
        window.open(source.href, "_blank", "noopener,noreferrer");
        return;
      }
      const attachmentId = (source.attachment_id || "").trim();
      if (!attachmentId) return;
      void (async () => {
        try {
          const blob = await downloadRoomMessageAttachmentBlob(attachmentId);
          const url = URL.createObjectURL(blob);
          const anchor = document.createElement("a");
          anchor.href = url;
          anchor.download = source.title || "attachment";
          anchor.rel = "noopener";
          anchor.click();
          URL.revokeObjectURL(url);
        } catch (err: unknown) {
          pushRoomNotice(
            err instanceof Error ? err.message : content.sharedLoadError,
            "error",
          );
        }
      })();
    },
    [content.sharedLoadError, pushRoomNotice],
  );

  const onAttachmentsSettled = useCallback(
    (messageId: string) => {
      bumpMessageAttachments(messageId);
      const id = roomId.trim();
      if (id) void reloadSharedItems(id);
    },
    [bumpMessageAttachments, reloadSharedItems, roomId],
  );

  const { initialLoading, refreshing } = resolveThreadLoadingState({
    loading,
    hasRoomSnapshot: Boolean(room),
  });

  return (
    <section
      className={
        variant === "page" ? "cm-page-stack" : "cm-interaction-room-host"
      }
    >
      {initialLoading ? (
        <CommercialLoadingCard title={content.roomLoadingLabel} variant="panel" />
      ) : null}
      {room ? (
        <>
          <KitInteractionRoomPage
            layout="thread"
            prefix="cm"
            labels={pageLabels}
            portalScopeClassName={CM_PORTAL_SCOPE}
            inboxQuery=""
            onInboxQueryChange={noopInboxQueryChange}
            chips={[]}
            rooms={[]}
            onRefresh={() => {
              const id = roomId.trim();
              if (!id) return;
              setLoading(true);
              void (async () => {
                try {
                  const [roomData, memberRows, messageRows, pinRows] =
                    await Promise.all([
                      getInteractionRoom(id),
                      listInteractionRoomMembers(id),
                      listInteractionMessages(id, { limit: 50 }),
                      listInteractionRoomPins(id),
                    ]);
                  setRoom(roomData);
                  onRoomTitle?.(roomData.title);
                  setMembers(memberRows);
                  setMessages([...messageRows].reverse());
                  setPinnedMessageIds(
                    new Set(pinRows.map((pin) => pin.message_id)),
                  );
                  void reloadSharedItems(id);
                } catch (err: unknown) {
                  pushRoomNotice(
                    err instanceof Error ? err.message : content.roomLoadError,
                    "error",
                  );
                } finally {
                  setLoading(false);
                }
              })();
            }}
            onSelectRoom={() => undefined}
            room={{
              id: room.id,
              title: room.title,
              chips: entityPresentation.chipLabel ? (
                <span
                  className={roomHeaderClasses.chip}
                  title={`${content.roomUnitChipTitle}: ${entityPresentation.chipLabel}`}
                >
                  {entityPresentation.chipLabel}
                </span>
              ) : undefined,
              titleActionLabel: entityHref
                ? content.roomOpenEntityAriaLabel
                : undefined,
              onTitleClick: entityHref
                ? () => {
                    navigatePluginPath(entityHref);
                  }
                : undefined,
              participants,
              participantsAriaLabel: content.roomMembersAriaLabel,
            }}
            onBack={
              inboxHref
                ? () => {
                    navigatePluginPath(inboxHref);
                  }
                : undefined
            }
            messages={threadMessages}
            messagesLoading={false}
            draft=""
            onDraftChange={noopDraftChange}
            onSubmit={noopSubmit}
            onFiles={(files) => addFilesRef.current(files)}
            accept={ROOM_ATTACH_ACCEPT}
            renderComposer={
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
                onMessageAttachmentsSettled={onAttachmentsSettled}
                onError={(message) => pushRoomNotice(message, "error")}
                onAddFilesReady={(addFiles) => {
                  addFilesRef.current = addFiles;
                }}
              />
            }
            resolveExtraActions={resolveExtraActions}
            resolveActionExtras={resolveActionExtras}
            onReply={(messageId) => {
              setEditingMessageId(null);
              setReplyMessageId(messageId);
            }}
            onTogglePin={(message) => {
              void onTogglePin(message.id, !message.pinned);
            }}
            onEdit={(message) => {
              setReplyMessageId(null);
              setEditingMessageId(message.id);
            }}
            onDelete={(messageId) => {
              void onDeleteMessage(messageId);
            }}
            onMentionActivate={(item, event) => {
              const href = (item.href ?? "").trim();
              if (!href) return;
              event.preventDefault();
              navigatePluginPath(href);
            }}
            resolveAttachmentImageSrc={(attachmentId) =>
              attachmentThumbUrls[attachmentId] ?? null
            }
            onAttachmentImageClick={(attachmentId) => {
              const row = attachmentMetaRef.current[attachmentId];
              if (!row) return;
              setInlinePreview({
                kind: "remote",
                id: row.id,
                fileName: row.file_name,
                contentType: row.content_type,
                byteSize: row.byte_size,
              });
            }}
            sharedItems={sharedItems}
            onOpenShared={onOpenShared}
            entityPrimary={entityPresentation.primaryNumber}
            entityFields={entityPresentation.aboutFields}
            entityHref={entityHref}
            onOpenEntity={
              entityHref
                ? () => {
                    navigatePluginPath(entityHref);
                  }
                : undefined
            }
            headerMenu={
              <InteractionRoomMoreMenu
                canRename
                canDelete={canManagePortfolios}
                renameDisabled={renamingRoom}
                deleteDisabled={deletingRoomId === roomId.trim()}
                onRename={() => setRenameDialogOpen(true)}
                onDelete={() => {
                  void onDeleteRoom();
                }}
              />
            }
            threadStatus={
              refreshing ? (
                <div
                  className="cm-room-thread__refresh"
                  role="status"
                  aria-live="polite"
                >
                  {content.roomRefreshingLabel}
                </div>
              ) : null
            }
          />
          <InteractionRoomRenameDialog
            open={renameDialogOpen}
            busy={renamingRoom}
            initialTitle={room.title}
            onClose={() => {
              if (!renamingRoom) setRenameDialogOpen(false);
            }}
            onSave={(title) => {
              void onRenameRoomSave(title);
            }}
          />
        </>
      ) : null}
      {!initialLoading && !room ? (
        <CommercialEmptyState
          title={content.roomFallbackTitle}
          message={content.roomMissingId}
        />
      ) : null}
      <TaskAttachmentPreviewModal
        open={Boolean(inlinePreview)}
        target={inlinePreview}
        onClose={() => setInlinePreview(null)}
      />
    </section>
  );
}

export { CommercialInteractionRoomHost as InteractionRoomPage };
