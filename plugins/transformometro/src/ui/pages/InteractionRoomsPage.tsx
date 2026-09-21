import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActionButton,
  FilePreviewModal,
  INTERACTION_ROOM_PAGE_LABELS_PT,
  InteractionRoomPage,
  markdownToPlainPreview,
  reactionLabelForCode,
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
import { useMyPersonProfilePhotoUrl } from "../../hooks/useMyPersonProfilePhotoUrl";
import { buildProcessoPath } from "../../utils/routeParser";
import { formatDateTime } from "../../utils/format";
import "./InteractionRoomsPage.css";

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
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<InteractionInboxFilter>("all");
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState<MentionComposerPendingAttachment[]>([]);
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
    return [...ids];
  }, [messages, shared]);

  const { nameFor: directoryNameFor } = useDirectoryUserLabels(authorIds, getAccessToken);
  const myPhotoUrl = useMyPersonProfilePhotoUrl(Boolean(meId), getAccessToken);

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

  const loadThread = useCallback(async () => {
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
    setMessages(nextMessages.items);
    setShared(nextFiles.items);
    setHasMore(nextMessages.has_more);
    setMessagesError(null);
  }, [getAccessToken, roomId]);

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
    setRoomError(null);
    setMessagesError(null);
    if (!roomId) return;
    void loadThread().catch((reason) => {
      if (cancelled) return;
      const message = errorText(reason, "Não foi possível abrir a sala.");
      setRoomError(message);
      setMessagesError(message);
    });
    return () => {
      cancelled = true;
    };
  }, [loadThread, roomId]);

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
      void loadThread()
        .then(() => loadRooms())
        .catch(() => undefined);
    }, 20000);
    return () => window.clearInterval(timer);
  }, [loadRooms, loadThread, roomId]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await loadRooms();
      if (roomId) await loadThread();
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

  async function send(markdown: string) {
    if (!roomId || sending) return;
    const content = markdown.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
    if (!resumeMessageId && !plainMessage(content)) {
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
    try {
      if (!messageId) {
        const mentions = mentionsRef.current.filter((item) =>
          content.toLowerCase().includes(`@${item.label.toLowerCase()}`),
        );
        const saved = await postInteractionMessage(roomId, content, getAccessToken, {
          parentId: replyId,
          mentions,
        });
        if (!saved.id || saved.room_id !== roomId || saved.content !== content) {
          throw new Error("O envio não confirmou a mensagem.");
        }
        messageId = saved.id;
        setMessages((current) => [...(current ?? []).filter((item) => item.id !== saved.id), saved]);
        setDraft("");
        setReplyId(null);
        mentionsRef.current = [];
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
      setMessages(nextMessages.items);
      setShared(nextFiles.items);
      setHasMore(nextMessages.has_more);
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
    const content = markdown.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
    if (!plainMessage(content)) {
      setActionError("A mensagem não pode ficar em branco.");
      return;
    }
    try {
      const saved = await editInteractionMessage(roomId, editingId, content, getAccessToken);
      if (saved.content !== content) throw new Error("A edição não confirmou a mensagem.");
      replaceMessage(saved);
      setEditingId(null);
      setEditDraft("");
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
          authorSrc: meId && item.author_user_id === meId ? myPhotoUrl : null,
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
              avatarSrc:
                meId && mention.user_id === meId ? myPhotoUrl ?? undefined : undefined,
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
    [authorName, meId, messages, myPhotoUrl, thumbUrls],
  );

  const speakers = useMemo(() => {
    const seen = new Map<string, string>();
    for (const item of messages ?? []) {
      if (!seen.has(item.author_user_id)) seen.set(item.author_user_id, authorName(item.author_user_id));
    }
    return [...seen.entries()].map(([id, name]) => ({
      id,
      name,
      src: meId && id === meId ? myPhotoUrl : null,
    }));
  }, [authorName, meId, messages, myPhotoUrl]);

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
    <TransformometroShell>
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
        editingId={editingId}
        editDraft={editDraft}
        onEditDraftChange={setEditDraft}
        onSaveEdit={(markdown) => void saveEdit(markdown)}
        onCancelEdit={() => {
          setEditingId(null);
          setEditDraft("");
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
        mentionHits={mentionHits}
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
                  kind: "user",
                  label: user.name,
                  subtitle: user.email,
                  avatarName: user.name,
                  avatarSrc: meId && user.id === meId ? myPhotoUrl ?? undefined : undefined,
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
          const fromShared = shared.find((item) => item.id === id);
          if (fromShared) {
            void openFile(fromShared);
            return;
          }
          for (const message of messages ?? []) {
            const hit = (message.attachments ?? []).find((item) => item.id === id);
            if (hit) {
              void openFile(hit);
              return;
            }
          }
        }}
        onRemoveAttachment={(id) => {
          const file = shared.find((item) => item.id === id);
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
