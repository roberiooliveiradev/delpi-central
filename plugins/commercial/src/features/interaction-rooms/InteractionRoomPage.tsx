import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ExternalLink, PanelRight, Search } from "lucide-react";
import { roomHeaderBemClasses } from "@delpi/plugin-ui/index";

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
import {
  CM_PORTAL_SCOPE,
  CommercialActionButton,
  CommercialAlertQueue,
  CommercialConversationFileDropLayer,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialMessageThread,
  CommercialRoomContextPanel,
  CommercialRoomHeader,
  CommercialRoomMessageFindPanel,
  CommercialRoomSidePanel,
  CommercialUnderlineNav,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { formatRoomEntityPresentation } from "./interactionRoomEntityPresentation";
import { InteractionRoomMessageComposer, ROOM_ATTACH_ACCEPT } from "./InteractionRoomMessageComposer";
import { InteractionRoomSharedView } from "./InteractionRoomSharedView";
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
  const roomHeaderClasses = useMemo(() => roomHeaderBemClasses("cm"), []);

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
  const [attachmentThumbUrls, setAttachmentThumbUrls] = useState<Record<string, string>>(
    {},
  );
  const [inlinePreview, setInlinePreview] = useState<TaskAttachmentPreviewTarget>(null);
  const attachmentMetaRef = useRef<Record<string, CommercialAttachmentDto>>({});
  const { currentUserId, myPortfolio } = usePortfolioScope();
  const sessionUserId = currentUserId ?? myPortfolio?.user_id ?? null;
  const confirm = useCommercialConfirm();
  const addFilesRef = useRef<(files: File[]) => void>(() => undefined);
  const msgsRef = useRef<HTMLDivElement | null>(null);
  const stickToBottomRef = useRef(true);
  const [sidePanelMode, setSidePanelMode] = useState<"context" | "find" | null>(
    null,
  );
  const [findQuery, setFindQuery] = useState("");
  const [findDebounced, setFindDebounced] = useState("");
  const [findResults, setFindResults] = useState<InteractionMessageDto[]>([]);
  const [findLoading, setFindLoading] = useState(false);
  const [roomView, setRoomView] = useState<"chat" | "shared">("chat");
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
      onMessageReactionsChange,
      pushRoomAlert,
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

  useEffect(() => {
    if (!sidePanelMode) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      setSidePanelMode(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [sidePanelMode]);

  useEffect(() => {
    const timer = window.setTimeout(() => setFindDebounced(findQuery.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [findQuery]);

  useEffect(() => {
    if (sidePanelMode !== "find") return;
    const id = roomId.trim();
    const q = findDebounced;
    if (!id || !q) {
      setFindResults([]);
      setFindLoading(false);
      return;
    }
    const controller = new AbortController();
    setFindLoading(true);
    void (async () => {
      try {
        const rows = await listInteractionMessages(id, {
          limit: 40,
          q,
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setFindResults(rows);
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        setFindResults([]);
        pushRoomAlert(
          err instanceof Error ? err.message : content.findInChatError,
          "danger",
        );
      } finally {
        if (!controller.signal.aborted) setFindLoading(false);
      }
    })();
    return () => controller.abort();
  }, [sidePanelMode, roomId, findDebounced, content.findInChatError]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "f") {
        return;
      }
      const target = event.target as HTMLElement | null;
      if (target?.closest?.("input, textarea, [contenteditable='true']")) {
        // Allow find-in-field; still intercept when focus is the thread surface.
        if (!target.closest(".cm-room-thread")) return;
      }
      if (!roomId.trim()) return;
      event.preventDefault();
      setSidePanelMode("find");
      setRoomView("chat");
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [roomId]);

  const findPanelResults = useMemo(() => {
    const now = new Date();
    return findResults.map((message) => {
      const created = message.created_at ? new Date(message.created_at) : null;
      const sameMonth =
        created &&
        !Number.isNaN(created.getTime()) &&
        created.getMonth() === now.getMonth() &&
        created.getFullYear() === now.getFullYear();
      return {
        id: message.id,
        messageId: message.id,
        authorLabel: nameFor(message.author_user_id) || message.author_user_id,
        dateLabel: formatInteractionMessageTime(message.created_at),
        bodyText: message.body_text || "",
        groupLabel: sameMonth
          ? content.findInChatThisMonth
          : created && !Number.isNaN(created.getTime())
            ? created.toLocaleDateString("pt-BR", {
                month: "long",
                year: "numeric",
              })
            : null,
      };
    });
  }, [findResults, nameFor, content.findInChatThisMonth]);

  const onSelectFindResult = useCallback(
    (messageId: string) => {
      setRoomView("chat");
      stickToBottomRef.current = false;
      window.requestAnimationFrame(() => {
        scrollThreadMessageIntoView(msgsRef.current, messageId);
      });
    },
    [],
  );

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
              chips={
                entityPresentation.chipLabel ? (
                  <span
                    className={roomHeaderClasses.chip}
                    title={`${content.roomUnitChipTitle}: ${entityPresentation.chipLabel}`}
                  >
                    {entityPresentation.chipLabel}
                  </span>
                ) : undefined
              }
              participants={participants}
              participantsAriaLabel={content.roomMembersAriaLabel}
              actions={
                <>
                  {entityHref ? (
                    <CommercialActionButton
                      variant="ghost"
                      aria-label={content.roomOpenEntityAriaLabel}
                      title={content.roomOpenEntityAriaLabel}
                      onClick={() => navigatePluginPath(entityHref)}
                    >
                      <ExternalLink size={16} aria-hidden />
                    </CommercialActionButton>
                  ) : null}
                  <CommercialActionButton
                    variant="ghost"
                    aria-label={content.findInChatAriaLabel}
                    title={content.findInChatAriaLabel}
                    aria-pressed={sidePanelMode === "find"}
                    onClick={() =>
                      setSidePanelMode((mode) =>
                        mode === "find" ? null : "find",
                      )
                    }
                  >
                    <Search size={16} aria-hidden />
                  </CommercialActionButton>
                  <CommercialActionButton
                    variant="ghost"
                    aria-label={
                      sidePanelMode === "context"
                        ? content.contextToggleCloseAriaLabel
                        : content.contextToggle
                    }
                    title={
                      sidePanelMode === "context"
                        ? content.contextToggleCloseAriaLabel
                        : content.contextToggle
                    }
                    aria-expanded={sidePanelMode === "context"}
                    aria-pressed={sidePanelMode === "context"}
                    onClick={() =>
                      setSidePanelMode((mode) =>
                        mode === "context" ? null : "context",
                      )
                    }
                  >
                    <PanelRight size={16} aria-hidden />
                  </CommercialActionButton>
                </>
              }
            />
          </div>
          <div className="cm-room-thread__view-nav">
            <CommercialUnderlineNav
              mode="tabs"
              aria-label={content.roomViewNavAriaLabel}
              activeId={roomView}
              items={[
                {
                  id: "chat",
                  label: content.roomViewChat,
                  controlId: "cm-room-view-chat",
                  tabId: "cm-room-tab-chat",
                  onSelect: () => setRoomView("chat"),
                },
                {
                  id: "shared",
                  label: content.roomViewShared,
                  controlId: "cm-room-view-shared",
                  tabId: "cm-room-tab-shared",
                  onSelect: () => setRoomView("shared"),
                },
              ]}
            />
          </div>
          <div className="cm-room-thread__body">
            {roomView === "shared" ? (
              <div
                id="cm-room-view-shared"
                role="tabpanel"
                aria-labelledby="cm-room-tab-shared"
                className="cm-room-thread__main"
              >
                <InteractionRoomSharedView
                  roomId={room.id}
                  onError={(message) => pushRoomAlert(message, "danger")}
                  onUploaded={() => {
                    /* list reloads internally; keep chat messages in sync via realtime */
                  }}
                />
              </div>
            ) : (
            <div
              id="cm-room-view-chat"
              role="tabpanel"
              aria-labelledby="cm-room-tab-chat"
              className="cm-room-thread__main"
            >
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
                    portalScopeClassName={CM_PORTAL_SCOPE}
                    actionsToolbarAriaLabel={content.messageActionsToolbarAriaLabel}
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
            )}
            <CommercialRoomSidePanel
              open={sidePanelMode != null}
              title={
                sidePanelMode === "find"
                  ? content.findInChatTitle
                  : content.contextToggle
              }
            >
              {sidePanelMode === "find" ? (
                <CommercialRoomMessageFindPanel
                  labels={{
                    title: content.findInChatTitle,
                    closeAriaLabel: content.findInChatCloseAriaLabel,
                    placeholder: content.findInChatPlaceholder,
                    clear: content.findInChatClear,
                    empty: content.findInChatEmpty,
                    loading: content.findInChatLoading,
                  }}
                  query={findQuery}
                  onQueryChange={setFindQuery}
                  onClear={() => {
                    setFindQuery("");
                    setFindResults([]);
                  }}
                  onClose={() => setSidePanelMode(null)}
                  results={findPanelResults}
                  loading={findLoading}
                  onSelectResult={onSelectFindResult}
                />
              ) : (
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
                  participants={participants}
                  participantsAriaLabel={content.roomMembersAriaLabel}
                  pins={contextPins}
                  onPinSelect={onSelectPin}
                />
              )}
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
      <TaskAttachmentPreviewModal
        open={Boolean(inlinePreview)}
        target={inlinePreview}
        onClose={() => setInlinePreview(null)}
      />
    </section>
  );
}
