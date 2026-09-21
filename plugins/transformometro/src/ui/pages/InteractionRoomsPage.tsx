import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActionButton,
  FilePreviewModal,
  INTERACTION_ROOM_PAGE_LABELS_PT,
  InteractionRoomPage,
  listInlinePendingIdsFromMarkdown,
  markdownToPlainPreview,
  reactionLabelForCode,
  rewriteInlinePendingInMarkdown,
  type InteractionRoomMessage,
  type InteractionRoomSharedItem,
  type MentionComposerPendingAttachment,
  type MentionMenuHit,
  type MentionTextItem,
  type ReactionBarItem,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PortalTopBar } from "../../components/TransformometroNav";
import { TRANSFORMOMETRO_ROUTES, buildInteractionRoomPath } from "../../constants/routes";
import { fetchMeProfile } from "../../data/api/meApi";
import { searchDirectoryUsers } from "../../data/api/transformometroMeetingMinutesApi";
import {
  INTERACTION_MESSAGE_MAX_LENGTH,
  deleteInteractionAttachment,
  deleteInteractionMessage,
  downloadInteractionAttachment,
  editInteractionMessage,
  getInteractionRoom,
  listInteractionAttachments,
  listInteractionMessages,
  listInteractionRooms,
  markInteractionRoomRead,
  pinInteractionMessage,
  postInteractionMessage,
  toggleInteractionReaction,
  uploadInteractionAttachment,
  type InteractionAttachmentDto,
  type InteractionInboxFilter,
  type InteractionMentionDto,
  type InteractionMessageDto,
  type InteractionRoomDto,
} from "../../data/api/transformometroInteractionApi";
import { useDirectoryUserLabels } from "../../hooks/useDirectoryUserLabels";
import { usePersonProfilePhotoUrls } from "../../hooks/usePersonProfilePhotoUrls";
import { buildProcessoPath } from "../../utils/routeParser";
import { formatDateTime } from "../../utils/format";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  roomId?: string;
  onNavigate: (path: string) => void;
};

const FILE_ACCEPT =
  "image/jpeg,image/png,image/webp,image/gif,application/pdf,text/plain,text/csv,.doc,.docx,.xls,.xlsx";
const LINK_PATTERN = /https?:\/\/[^\s<>"')\]]+/g;
const TM_PORTAL_SCOPE = "dashboard-transformometro";

function errorText(reason: unknown, fallback: string): string {
  return reason instanceof Error && reason.message ? reason.message : fallback;
}

function plainMessage(value: string): string {
  return markdownToPlainPreview(value, INTERACTION_MESSAGE_MAX_LENGTH).trim();
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function isImageAttachment(file: Pick<InteractionAttachmentDto, "content_type" | "file_name">): boolean {
  const ct = (file.content_type || "").toLowerCase();
  if (ct.startsWith("image/")) return true;
  return /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(file.file_name || "");
}

function reactionItems(message: InteractionMessageDto, meId: string | null): ReactionBarItem[] {
  const grouped = new Map<string, ReactionBarItem>();
  for (const reaction of message.reactions ?? []) {
    const current = grouped.get(reaction.code) ?? {
      code: reaction.code,
      label: reactionLabelForCode(reaction.code),
      count: 0,
      reactedByMe: false,
    };
    current.count += 1;
    if (meId && reaction.user_id === meId) current.reactedByMe = true;
    grouped.set(reaction.code, current);
  }
  return [...grouped.values()];
}

/** Keep older pages already loaded; refresh the latest page without wiping history. */
function mergePollMessages(
  current: InteractionMessageDto[],
  latest: InteractionMessageDto[],
): InteractionMessageDto[] {
  if (latest.length === 0) return current;
  const latestIds = new Set(latest.map((item) => item.id));
  const oldestLatestId = latest[0]?.id;
  const cursorIndex = oldestLatestId
    ? current.findIndex((item) => item.id === oldestLatestId)
    : -1;
  const older =
    cursorIndex > 0
      ? current.slice(0, cursorIndex).filter((item) => !latestIds.has(item.id))
      : current.filter((item) => !latestIds.has(item.id));
  return [...older, ...latest];
}

type PreviewTarget = {
  id: string;
  fileName: string;
  contentType: string;
  byteSize: number;
  blob: Blob;
};

export function InteractionRoomsPage({ getAccessToken, pathname, roomId, onNavigate }: Props) {
  const mentionsRef = useRef<InteractionMentionDto[]>([]);
  const [rooms, setRooms] = useState<InteractionRoomDto[] | null>(null);
  const [roomsError, setRoomsError] = useState<string | null>(null);
  const [room, setRoom] = useState<InteractionRoomDto | null>(null);
  const [roomError, setRoomError] = useState<string | null>(null);
  const [messages, setMessages] = useState<InteractionMessageDto[] | null>(null);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [shared, setShared] = useState<InteractionAttachmentDto[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<InteractionInboxFilter>("all");
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState<MentionComposerPendingAttachment[]>([]);
  const [inlineFiles, setInlineFiles] = useState<Record<string, File>>({});
  const [inlineThumbUrls, setInlineThumbUrls] = useState<Record<string, string>>({});
  const [resumeMessageId, setResumeMessageId] = useState<string | null>(null);
  const [replyId, setReplyId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState("");
  const [mentionHits, setMentionHits] = useState<MentionMenuHit[]>([]);
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [meId, setMeId] = useState<string | null>(null);
  const [meName, setMeName] = useState<string | null>(null);
  const [thumbUrls, setThumbUrls] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<PreviewTarget | null>(null);
  const nameCacheRef = useRef<Record<string, string>>({});

  const clearInlinePending = useCallback(() => {
    setInlineFiles({});
    setInlineThumbUrls((previous) => {
      for (const url of Object.values(previous)) URL.revokeObjectURL(url);
      return {};
    });
  }, []);

  useEffect(() => {
    void fetchMeProfile(getAccessToken)
      .then((profile) => {
        setMeId(profile.id || null);
        setMeName(profile.name?.trim() || null);
      })
      .catch(() => undefined);
  }, [getAccessToken]);

  const authorIds = useMemo(() => {
    const ids = new Set<string>();
    for (const item of messages ?? []) {
      if (item.author_user_id) ids.add(item.author_user_id);
      for (const mention of item.mentions ?? []) {
        if (mention.user_id) ids.add(mention.user_id);
      }
    }
    for (const file of shared) {
      if (file.uploaded_by_user_id) ids.add(file.uploaded_by_user_id);
    }
    for (const hit of mentionHits) {
      if (hit.id) ids.add(hit.id);
    }
    if (meId) ids.add(meId);
    return [...ids];
  }, [meId, mentionHits, messages, shared]);

  const { nameFor: directoryNameFor } = useDirectoryUserLabels(authorIds, getAccessToken);
  const { photoFor } = usePersonProfilePhotoUrls(authorIds, getAccessToken);

  const authorName = useCallback(
    (authorUserId: string, fallback?: string | null) => {
      const cached = nameCacheRef.current[authorUserId];
      if (cached) return cached;
      if (meId && authorUserId === meId && meName) return meName;
      return directoryNameFor(authorUserId, fallback);
    },
    [directoryNameFor, meId, meName],
  );

  useEffect(() => {
    for (const item of messages ?? []) {
      for (const mention of item.mentions ?? []) {
        const label = (mention.label ?? "").replace(/^@/, "").trim();
        if (mention.user_id && label) nameCacheRef.current[mention.user_id] = label;
      }
    }
  }, [messages]);

  useEffect(() => {
    if (!roomId || !messages) {
      setThumbUrls((previous) => {
        for (const url of Object.values(previous)) URL.revokeObjectURL(url);
        return {};
      });
      return;
    }
    let cancelled = false;
    const created: string[] = [];
    const imageFiles = messages.flatMap((item) =>
      (item.attachments ?? []).filter((file) => isImageAttachment(file)),
    );
    void (async () => {
      const next: Record<string, string> = {};
      for (const file of imageFiles) {
        try {
          const blob = await downloadInteractionAttachment(roomId, file.id, getAccessToken);
          if (cancelled) return;
          const url = URL.createObjectURL(blob);
          created.push(url);
          next[file.id] = url;
        } catch {
          /* prévia opcional */
        }
      }
      if (cancelled) {
        for (const url of created) URL.revokeObjectURL(url);
        return;
      }
      setThumbUrls((previous) => {
        for (const url of Object.values(previous)) URL.revokeObjectURL(url);
        return next;
      });
      created.length = 0;
    })();
    return () => {
      cancelled = true;
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [getAccessToken, messages, roomId]);

  const loadRooms = useCallback(async () => {
    const page = await listInteractionRooms(getAccessToken, filter);
    setRooms(page.items);
    setRoomsError(null);
  }, [filter, getAccessToken]);

  const loadThread = useCallback(
    async (mode: "replace" | "poll" = "replace") => {
      if (!roomId) {
        setRoom(null);
        setRoomError(null);
        setMessages(null);
        setMessagesError(null);
        setShared([]);
        setHasMore(false);
        return;
      }
      const [nextRoom, nextMessages, nextFiles] = await Promise.all([
        getInteractionRoom(roomId, getAccessToken),
        listInteractionMessages(roomId, getAccessToken),
        listInteractionAttachments(roomId, getAccessToken),
      ]);
      setRoom(nextRoom);
      setRoomError(null);
      if (mode === "poll") {
        setMessages((current) => mergePollMessages(current ?? [], nextMessages.items));
      } else {
        setMessages(nextMessages.items);
        setHasMore(nextMessages.has_more);
      }
      setShared(nextFiles.items);
      setMessagesError(null);
    },
    [getAccessToken, roomId],
  );

  const loadOlder = useCallback(async () => {
    if (!roomId || loadingOlder || !hasMore) return;
    const oldestId = messages?.[0]?.id;
    if (!oldestId) return;
    setLoadingOlder(true);
    try {
      const page = await listInteractionMessages(roomId, getAccessToken, { beforeId: oldestId });
      const incomingIds = new Set(page.items.map((item) => item.id));
      setMessages((current) => [
        ...page.items,
        ...(current ?? []).filter((item) => !incomingIds.has(item.id)),
      ]);
      setHasMore(page.has_more);
      setMessagesError(null);
    } catch (reason) {
      setMessagesError(errorText(reason, "Não foi possível carregar mensagens anteriores."));
    } finally {
      setLoadingOlder(false);
    }
  }, [getAccessToken, hasMore, loadingOlder, messages, roomId]);

  useEffect(() => {
    let cancelled = false;
    setRooms(null);
    setRoomsError(null);
    void loadRooms().catch((reason) => {
      if (cancelled) return;
      setRooms([]);
      setRoomsError(errorText(reason, "Não foi possível carregar as salas."));
    });
    return () => {
      cancelled = true;
    };
  }, [loadRooms]);

  useEffect(() => {
    let cancelled = false;
    setDraft("");
    setPending([]);
    clearInlinePending();
    setResumeMessageId(null);
    setReplyId(null);
    setEditingId(null);
    setEditDraft("");
    mentionsRef.current = [];
    setSendError(null);
    setActionError(null);
    setRoom(null);
    setMessages(null);
    setShared([]);
    setHasMore(false);
    setLoadingOlder(false);
    setRoomError(null);
    setMessagesError(null);
    if (!roomId) return;
    void loadThread("replace").catch((reason) => {
      if (cancelled) return;
      const message = errorText(reason, "Não foi possível abrir a sala.");
      setRoomError(message);
      setMessagesError(message);
    });
    return () => {
      cancelled = true;
    };
  }, [clearInlinePending, loadThread, roomId]);

  useEffect(() => {
    if (!roomId) return;
    let cancelled = false;
    void markInteractionRoomRead(roomId, getAccessToken)
      .then(() => {
        if (!cancelled) return loadRooms();
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [getAccessToken, loadRooms, roomId]);

  useEffect(() => {
    if (!roomId) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState !== "visible") return;
      void loadThread("poll")
        .then(() => loadRooms())
        .catch(() => undefined);
    }, 20000);
    return () => window.clearInterval(timer);
  }, [loadRooms, loadThread, roomId]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await loadRooms();
      if (roomId) await loadThread("replace");
    } catch (reason) {
      const message = errorText(reason, "Não foi possível atualizar.");
      if (roomId) setMessagesError(message);
      else setRoomsError(message);
    } finally {
      setRefreshing(false);
    }
  }, [loadRooms, loadThread, roomId]);

  const replaceMessage = useCallback((next: InteractionMessageDto) => {
    setMessages((current) => (current ?? []).map((item) => (item.id === next.id ? next : item)));
  }, []);

  const onInlineImagesInserted = useCallback(
    (items: readonly { pendingId: string; file: File }[]) => {
      if (items.length === 0) return;
      setInlineFiles((previous) => {
        const next = { ...previous };
        for (const item of items) next[item.pendingId] = item.file;
        return next;
      });
      setInlineThumbUrls((previous) => {
        const next = { ...previous };
        for (const item of items) {
          if (next[item.pendingId]) continue;
          next[item.pendingId] = URL.createObjectURL(item.file);
        }
        return next;
      });
    },
    [],
  );

  const onInlineImageRemoved = useCallback((pendingId: string) => {
    setInlineFiles((previous) => {
      if (!(pendingId in previous)) return previous;
      const next = { ...previous };
      delete next[pendingId];
      return next;
    });
    setInlineThumbUrls((previous) => {
      const url = previous[pendingId];
      if (!url) return previous;
      URL.revokeObjectURL(url);
      const next = { ...previous };
      delete next[pendingId];
      return next;
    });
  }, []);

  const resolveAttachmentImageSrc = useCallback(
    (attachmentId: string) => inlineThumbUrls[attachmentId] ?? thumbUrls[attachmentId] ?? null,
    [inlineThumbUrls, thumbUrls],
  );

  function addFiles(files: File[]) {
    if (files.length === 0) return;
    setPending((current) => {
      const next = [...current];
      for (const file of files) {
        if (next.length >= 5) break;
        next.push({
          id: crypto.randomUUID(),
          fileName: file.name,
          contentType: file.type,
          file,
        });
      }
      return next;
    });
  }

  async function uploadInlineAndRewrite(messageId: string, bodyText: string): Promise<string> {
    if (!roomId) return bodyText;
    const pendingIds = listInlinePendingIdsFromMarkdown(bodyText);
    if (pendingIds.length === 0) return bodyText;
    const pendingToUuid: Record<string, string> = {};
    for (const pendingId of pendingIds) {
      const file = inlineFiles[pendingId];
      if (!file) {
        throw new Error("Uma imagem colada não pôde ser enviada. Remova-a e cole novamente.");
      }
      const uploaded = await uploadInteractionAttachment(roomId, messageId, file, getAccessToken);
      pendingToUuid[pendingId] = uploaded.id;
    }
    const rewritten = rewriteInlinePendingInMarkdown(bodyText, pendingToUuid);
    if (listInlinePendingIdsFromMarkdown(rewritten).length > 0) {
      throw new Error("Uma imagem colada não pôde ser enviada. Remova-a e cole novamente.");
    }
    return rewritten;
  }

  async function send(markdown: string) {
    if (!roomId || sending) return;
    const content = markdown.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const inlinePending = listInlinePendingIdsFromMarkdown(content);
    const hasBody = Boolean(plainMessage(content) || inlinePending.length > 0 || pending.length > 0);
    if (!resumeMessageId && !hasBody) {
      setSendError("A mensagem não pode ficar em branco.");
      return;
    }
    if (content.length > INTERACTION_MESSAGE_MAX_LENGTH) {
      setSendError(`A mensagem pode ter no máximo ${INTERACTION_MESSAGE_MAX_LENGTH} caracteres.`);
      return;
    }
    setSending(true);
    setSendError(null);
    let messageId = resumeMessageId;
    let bodyText = content.trim() || (inlinePending.length > 0 || pending.length > 0 ? content : "");
    try {
      if (!messageId) {
        const mentions = mentionsRef.current.filter((item) =>
          bodyText.toLowerCase().includes(`@${item.label.toLowerCase()}`),
        );
        const saved = await postInteractionMessage(roomId, bodyText, getAccessToken, {
          parentId: replyId,
          mentions,
        });
        if (!saved.id || saved.room_id !== roomId) {
          throw new Error("O envio não confirmou a mensagem.");
        }
        messageId = saved.id;
        setMessages((current) => [...(current ?? []).filter((item) => item.id !== saved.id), saved]);
        setDraft("");
        setReplyId(null);
        mentionsRef.current = [];
      }
      if (listInlinePendingIdsFromMarkdown(bodyText).length > 0) {
        bodyText = await uploadInlineAndRewrite(messageId, bodyText);
        const rewritten = await editInteractionMessage(roomId, messageId, bodyText, getAccessToken);
        replaceMessage(rewritten);
        clearInlinePending();
      }
      const remaining: MentionComposerPendingAttachment[] = [];
      let uploadFailed = false;
      for (const item of pending) {
        if (uploadFailed || !item.file) {
          remaining.push(item);
          continue;
        }
        try {
          await uploadInteractionAttachment(roomId, messageId, item.file, getAccessToken);
        } catch (reason) {
          uploadFailed = true;
          remaining.push(item);
          setSendError(errorText(reason, "A mensagem foi enviada, mas um anexo não foi gravado."));
        }
      }
      setPending(remaining);
      setResumeMessageId(uploadFailed ? messageId : null);
      const [nextMessages, nextFiles] = await Promise.all([
        listInteractionMessages(roomId, getAccessToken),
        listInteractionAttachments(roomId, getAccessToken),
      ]);
      setMessages((current) => mergePollMessages(current ?? [], nextMessages.items));
      setShared(nextFiles.items);
      setMessagesError(null);
      void loadRooms().catch(() => undefined);
    } catch (reason) {
      setSendError(errorText(reason, "Não foi possível enviar a mensagem."));
    } finally {
      setSending(false);
    }
  }

  async function saveEdit(markdown: string) {
    if (!roomId || !editingId) return;
    const content = markdown.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const inlinePending = listInlinePendingIdsFromMarkdown(content);
    if (!plainMessage(content) && inlinePending.length === 0) {
      setActionError("A mensagem não pode ficar em branco.");
      return;
    }
    try {
      let bodyText = content;
      if (inlinePending.length > 0) {
        bodyText = await uploadInlineAndRewrite(editingId, bodyText);
      }
      const saved = await editInteractionMessage(roomId, editingId, bodyText, getAccessToken);
      if (saved.content !== bodyText) throw new Error("A edição não confirmou a mensagem.");
      replaceMessage(saved);
      setEditingId(null);
      setEditDraft("");
      clearInlinePending();
      setActionError(null);
    } catch (reason) {
      setActionError(errorText(reason, "Não foi possível editar a mensagem."));
    }
  }

  async function removeMessage(messageId: string) {
    if (!roomId) return;
    if (!window.confirm("Remover esta mensagem?")) return;
    try {
      const saved = await deleteInteractionMessage(roomId, messageId, getAccessToken);
      replaceMessage(saved);
      setActionError(null);
    } catch (reason) {
      setActionError(errorText(reason, "Não foi possível remover a mensagem."));
    }
  }

  async function react(messageId: string, code: string) {
    if (!roomId) return;
    try {
      replaceMessage(await toggleInteractionReaction(roomId, messageId, code, getAccessToken));
      setActionError(null);
    } catch (reason) {
      setActionError(errorText(reason, "Não foi possível registrar a reação."));
    }
  }

  async function togglePin(message: InteractionMessageDto) {
    if (!roomId) return;
    try {
      replaceMessage(await pinInteractionMessage(roomId, message.id, !message.pinned, getAccessToken));
      setActionError(null);
    } catch (reason) {
      setActionError(errorText(reason, "Não foi possível fixar a mensagem."));
    }
  }

  async function openFile(file: InteractionAttachmentDto) {
    if (!roomId) return;
    try {
      const blob = await downloadInteractionAttachment(roomId, file.id, getAccessToken);
      setPreview({
        id: file.id,
        fileName: file.file_name,
        contentType: file.content_type,
        byteSize: file.byte_size,
        blob,
      });
      setActionError(null);
    } catch (reason) {
      setActionError(errorText(reason, "Não foi possível abrir o arquivo."));
    }
  }

  function findAttachment(id: string): InteractionAttachmentDto | undefined {
    const fromShared = shared.find((item) => item.id === id);
    if (fromShared) return fromShared;
    for (const message of messages ?? []) {
      const hit = (message.attachments ?? []).find((item) => item.id === id);
      if (hit) return hit;
    }
    return undefined;
  }

  async function removeFile(file: InteractionAttachmentDto) {
    if (!roomId) return;
    if (!window.confirm("Remover este arquivo?")) return;
    try {
      await deleteInteractionAttachment(roomId, file.id, getAccessToken);
      setShared((current) => current.filter((item) => item.id !== file.id));
      setMessages((current) =>
        (current ?? []).map((item) =>
          item.id === file.message_id
            ? { ...item, attachments: (item.attachments ?? []).filter((entry) => entry.id !== file.id) }
            : item,
        ),
      );
      setActionError(null);
    } catch (reason) {
      setActionError(errorText(reason, "Não foi possível remover o arquivo."));
    }
  }

  const visibleRooms = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (rooms ?? []).filter((item) => {
      if (filter === "process" && !item.processo_id) return false;
      if (!needle) return true;
      const haystack = `${item.processo_nome} ${item.processo_codigo} ${item.last_message_preview ?? ""}`.toLowerCase();
      return haystack.includes(needle);
    });
  }, [filter, query, rooms]);

  const threadItems = useMemo<InteractionRoomMessage[]>(
    () =>
      (messages ?? []).map((item) => {
        const removed = Boolean(item.deleted_at);
        return {
          id: item.id,
          kind: "text",
          bodyText: removed ? "Mensagem removida." : item.content,
          createdAtLabel: item.edited_at
            ? `${formatDateTime(item.created_at)} · editada`
            : formatDateTime(item.created_at),
          authorName: authorName(item.author_user_id),
          authorUserId: item.author_user_id,
          authorSrc: photoFor(item.author_user_id),
          parentId: item.parent_id,
          mine: Boolean(meId && item.author_user_id === meId),
          deleted: removed,
          pinned: Boolean(item.pinned),
          mentions: (item.mentions ?? []).map((mention) => {
            const label = (mention.label ?? "").replace(/^@/, "").trim() || mention.label;
            const resolved = authorName(mention.user_id, label);
            return {
              kind: "user",
              id: mention.user_id,
              label,
              avatarName: resolved,
              title: `Menção: ${resolved}`,
              avatarSrc: photoFor(mention.user_id) ?? undefined,
            };
          }),
          reactions: reactionItems(item, meId),
          files: (item.attachments ?? []).map((file) => ({
            id: file.id,
            fileName: file.file_name,
            contentType: file.content_type,
            previewUrl: thumbUrls[file.id] ?? null,
            detail: formatBytes(file.byte_size),
            removable: Boolean(meId && file.uploaded_by_user_id === meId),
          })),
        };
      }),
    [authorName, meId, messages, photoFor, thumbUrls],
  );

  const speakers = useMemo(() => {
    const seen = new Map<string, string>();
    for (const item of messages ?? []) {
      if (!seen.has(item.author_user_id)) seen.set(item.author_user_id, authorName(item.author_user_id));
    }
    return [...seen.entries()].map(([id, name]) => ({
      id,
      name,
      src: photoFor(id),
    }));
  }, [authorName, messages, photoFor]);

  const sharedItems = useMemo<InteractionRoomSharedItem[]>(() => {
    const files: InteractionRoomSharedItem[] = shared.map((file) => ({
      id: file.id,
      kind: "file",
      title: file.file_name,
      subtitle: file.content_type,
      whenLabel: file.created_at ? formatDateTime(file.created_at) : null,
      whoLabel: authorName(file.uploaded_by_user_id),
      ariaLabel: `Abrir ${file.file_name}`,
    }));
    const links: InteractionRoomSharedItem[] = [];
    for (const item of messages ?? []) {
      if (item.deleted_at) continue;
      const seen = new Set<string>();
      for (const match of item.content.matchAll(LINK_PATTERN)) {
        const href = match[0].replace(/[.,;:]+$/, "");
        if (!href || seen.has(href)) continue;
        seen.add(href);
        links.push({
          id: `${item.id}:${href}`,
          kind: "link",
          title: href,
          href,
          whenLabel: formatDateTime(item.created_at),
          whoLabel: authorName(item.author_user_id),
          ariaLabel: `Abrir ${href}`,
        });
      }
    }
    return [...files, ...links];
  }, [authorName, messages, shared]);

  const mentionHitsWithPhotos = useMemo(
    () =>
      mentionHits.map((hit) => ({
        ...hit,
        avatarSrc: photoFor(hit.id) ?? undefined,
      })),
    [mentionHits, photoFor],
  );

  const replyTarget = (messages ?? []).find((item) => item.id === replyId) ?? null;
  const searchEmpty = query.trim().length > 0 && (rooms?.length ?? 0) > 0 && visibleRooms.length === 0;
  const emptyTitle = searchEmpty
    ? "Nenhuma sala com esse título"
    : filter === "unread"
      ? "Nenhuma sala com mensagem nova"
      : filter === "mentioned"
        ? "Nenhuma menção nova"
        : undefined;
  const emptyMessage = searchEmpty
    ? "Tente outro nome ou código de processo."
    : filter === "unread"
      ? "Quando alguém escrever em uma sala que você já abriu, ela aparece aqui."
      : filter === "mentioned"
        ? "Quando alguém mencionar você, a sala aparece aqui."
        : "Abra um processo para iniciar uma interação.";

  return (
    <TransformometroShell fillViewport>
      <PortalTopBar currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.interactionRooms} onNavigate={onNavigate} />
      <InteractionRoomPage
        labels={{
          ...INTERACTION_ROOM_PAGE_LABELS_PT,
          context: {
            ...INTERACTION_ROOM_PAGE_LABELS_PT.context,
            openEntity: "Abrir processo",
          },
        }}
        inboxQuery={query}
        onInboxQueryChange={setQuery}
        chips={[
          { id: "all", label: "Todas", active: filter === "all", onSelect: () => setFilter("all") },
          { id: "unread", label: "Não lidas", active: filter === "unread", onSelect: () => setFilter("unread") },
          { id: "mentioned", label: "Menções", active: filter === "mentioned", onSelect: () => setFilter("mentioned") },
          { id: "process", label: "Processos", active: filter === "process", onSelect: () => setFilter("process") },
        ]}
        rooms={visibleRooms.map((item) => ({
          id: item.id,
          title: item.processo_nome || item.processo_codigo || "Processo",
          preview: item.last_message_preview ? markdownToPlainPreview(item.last_message_preview) : null,
          metaLabel: item.last_message_at ? formatDateTime(item.last_message_at) : null,
          kindLabel: "Processo",
          unreadCount: item.unread_count ?? 0,
          mentioned: item.mentioned,
          selected: item.id === roomId,
        }))}
        roomsLoading={rooms === null}
        roomsRefreshing={refreshing}
        roomsError={roomsError ? `Não foi possível carregar as salas. ${roomsError}` : null}
        inboxEmptyTitle={emptyTitle}
        inboxEmptyMessage={emptyMessage}
        inboxEmptyAction={
          searchEmpty || filter === "unread" || filter === "mentioned" ? undefined : (
            <ActionButton type="button" onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.processes)}>
              Meus processos
            </ActionButton>
          )
        }
        onRefresh={() => void refresh()}
        onSelectRoom={(id) => onNavigate(buildInteractionRoomPath(id))}
        inboxSubtitle={(row) => visibleRooms.find((item) => item.id === row.id)?.processo_codigo || "Processo"}
        room={
          roomId
            ? {
                id: roomId,
                title: room?.processo_nome || "Processo",
                chips: room?.processo_codigo ? <span>{room.processo_codigo}</span> : undefined,
                titleActionLabel: "Abrir processo",
                onTitleClick: room ? () => onNavigate(buildProcessoPath(room.processo_id)) : undefined,
                participants: speakers,
                participantsAriaLabel: "Quem falou",
              }
            : null
        }
        onBack={() => onNavigate(TRANSFORMOMETRO_ROUTES.interactionRooms)}
        messages={threadItems}
        messagesLoading={Boolean(roomId) && messages === null && !messagesError}
        messagesError={messagesError ? `Não foi possível carregar as mensagens. ${messagesError}` : roomError}
        composerError={sendError}
        actionError={actionError}
        hasMore={hasMore}
        onLoadOlder={() => void loadOlder()}
        loadingOlder={loadingOlder}
        editingId={editingId}
        editDraft={editDraft}
        onEditDraftChange={setEditDraft}
        onSaveEdit={(markdown) => void saveEdit(markdown)}
        onCancelEdit={() => {
          setEditingId(null);
          setEditDraft("");
          clearInlinePending();
        }}
        portalScopeClassName={TM_PORTAL_SCOPE}
        draft={draft}
        onDraftChange={setDraft}
        onSubmit={(markdown) => void send(markdown)}
        submitting={sending}
        pendingAttachments={pending}
        onFiles={addFiles}
        onRemovePendingAttachment={(id) => setPending((current) => current.filter((item) => item.id !== id))}
        accept={FILE_ACCEPT}
        resolveAttachmentImageSrc={resolveAttachmentImageSrc}
        onAttachmentImageClick={(id) => {
          const file = findAttachment(id);
          if (file) void openFile(file);
        }}
        onInlineImagesInserted={onInlineImagesInserted}
        onInlineImageRemoved={onInlineImageRemoved}
        mentionHits={mentionHitsWithPhotos}
        onMentionQueryChange={(next) => {
          if (!next?.trim()) {
            setMentionHits([]);
            return;
          }
          void searchDirectoryUsers(next.trim(), 8, undefined, getAccessToken)
            .then((users) => {
              for (const user of users) {
                if (user.id && user.name) nameCacheRef.current[user.id] = user.name;
              }
              setMentionHits(
                users.map((user) => ({
                  id: user.id,
                  kind: "user" as const,
                  label: user.name,
                  subtitle: user.email,
                  avatarName: user.name,
                })),
              );
            })
            .catch(() => setMentionHits([]));
        }}
        onMentionInserted={(hit) => {
          const label = hit.label.replace(/^@/, "").trim();
          if (!label) return;
          nameCacheRef.current[hit.id] = label;
          mentionsRef.current = [
            ...mentionsRef.current.filter((item) => item.user_id !== hit.id),
            { user_id: hit.id, label },
          ];
        }}
        onMentionActivate={(_item: MentionTextItem) => {
          /* Chip ativável (acessível); TM não tem perfil de usuário próprio. */
        }}
        replyTo={
          replyTarget
            ? {
                label: "Respondendo",
                preview: markdownToPlainPreview(replyTarget.deleted_at ? "Mensagem removida." : replyTarget.content),
              }
            : null
        }
        onCancelReply={() => setReplyId(null)}
        onReply={(id) => {
          setReplyId(id);
          setEditingId(null);
        }}
        onTogglePin={(message) => {
          const source = (messages ?? []).find((item) => item.id === message.id);
          if (source) void togglePin(source);
        }}
        onEdit={(message) => {
          const source = (messages ?? []).find((item) => item.id === message.id);
          if (!source) return;
          setEditingId(source.id);
          setEditDraft(source.content);
        }}
        onDelete={(id) => void removeMessage(id)}
        onToggleReaction={(id, code) => void react(id, code)}
        onOpenAttachment={(id) => {
          const file = findAttachment(id);
          if (file) void openFile(file);
        }}
        onRemoveAttachment={(id) => {
          const file = findAttachment(id);
          if (file) void removeFile(file);
        }}
        sharedItems={sharedItems}
        onOpenShared={(item) => {
          if (item.kind === "link" && item.href) {
            window.open(item.href, "_blank", "noopener,noreferrer");
            return;
          }
          const file = shared.find((entry) => entry.id === item.id);
          if (file) void openFile(file);
        }}
        entityPrimary={room?.processo_codigo || null}
        entityFields={room ? [{ label: "Processo", value: room.processo_nome }] : []}
        entityHref={room ? buildProcessoPath(room.processo_id) : null}
        onOpenEntity={room ? () => onNavigate(buildProcessoPath(room.processo_id)) : undefined}
        onCopyLink={() => void navigator.clipboard.writeText(window.location.href)}
        threadStatus={refreshing ? <p role="status">Atualizando mensagens…</p> : null}
      />
      <FilePreviewModal
        open={Boolean(preview)}
        title={preview?.fileName ?? "Arquivo"}
        onClose={() => setPreview(null)}
        portalScopeClassName={TM_PORTAL_SCOPE}
        source={preview?.blob}
        fileName={preview?.fileName}
        mimeType={preview?.contentType}
        metaItems={
          preview
            ? [preview.contentType, formatBytes(preview.byteSize)]
            : undefined
        }
      />
    </TransformometroShell>
  );
}
