import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, MessageSquare, Pencil, Pin, RefreshCw, Reply, Search, Trash2 } from "lucide-react";
import {
  ActionButton,
  CatalogSearchBar,
  EmptyGuidance,
  InitialsAvatar,
  MentionComposer,
  MessageThread,
  ReactionBar,
  ResizableColumns,
  RoomConversationChatColumn,
  RoomConversationShell,
  RoomHeader,
  RoomInboxList,
  RoomInboxPanel,
  RoomMessageFindPanel,
  RoomSharedItemList,
  ScopeChipBar,
  SectionCard,
  SegmentToggle,
  catalogSearchBarBemClasses,
  conversationFileDropLayerBemClasses,
  emptyGuidanceBemClasses,
  initialsAvatarBemClasses,
  markdownToPlainPreview,
  mentionComposerBemClasses,
  messageThreadBemClasses,
  reactionBarBemClasses,
  resizableColumnsBemClasses,
  roomConversationShellBemClasses,
  roomHeaderBemClasses,
  roomInboxListBemClasses,
  roomMessageFindPanelBemClasses,
  roomSharedItemListBemClasses,
  scopeChipBarBemClasses,
  sectionCardPacBemClasses,
  segmentToggleBemClasses,
  type MentionComposerPendingAttachment,
  type MentionMenuHit,
  type MessageThreadItem,
  type ReactionBarItem,
  type RoomInboxListItem,
  type RoomSharedItem,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
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
import { buildProcessoPath } from "../../utils/routeParser";
import { formatDateTime } from "../../utils/format";
import "./InteractionRoomsPage.css";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  roomId?: string;
  onNavigate: (path: string) => void;
};

type RoomPane = "chat" | "files";

const SECTION = sectionCardPacBemClasses("ds");
const SECTION_LABELS = { titleHelpAriaLabel: (title: string) => title };
const SEARCH = catalogSearchBarBemClasses("ds");
const CHIPS = scopeChipBarBemClasses("ds");
const INBOX = roomInboxListBemClasses("ds");
const AVATAR = initialsAvatarBemClasses("ds");
const HEADER = roomHeaderBemClasses("ds");
const THREAD = messageThreadBemClasses("ds");
const SHELL = roomConversationShellBemClasses("ds");
const DROP = conversationFileDropLayerBemClasses("ds");
const COLUMNS = resizableColumnsBemClasses("ds");
const EMPTY = emptyGuidanceBemClasses("ds");
const COMPOSER = mentionComposerBemClasses("ds");
const REACTIONS = reactionBarBemClasses("ds");
const SHARED = roomSharedItemListBemClasses("ds");
const FIND = roomMessageFindPanelBemClasses("ds");
const SEGMENTS = segmentToggleBemClasses("ds");
const FILE_ACCEPT =
  "image/jpeg,image/png,image/webp,image/gif,application/pdf,text/plain,text/csv,.doc,.docx,.xls,.xlsx";

const COMPOSER_LABELS = {
  placeholder: "Escreva uma mensagem…",
  sendAriaLabel: "Enviar",
  attachAriaLabel: "Anexar arquivo",
  mentionListAriaLabel: "Pessoas",
  mentionEmptyLabel: "Nenhuma pessoa para mencionar",
  formatToggleAriaLabel: "Formatação",
  replyCancelAriaLabel: "Cancelar resposta",
};

function errorText(reason: unknown, fallback: string): string {
  return reason instanceof Error && reason.message ? reason.message : fallback;
}

function useNarrowWorkspace() {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 900px)");
    const apply = () => setNarrow(media.matches);
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, []);
  return narrow;
}

function plainMessage(value: string): string {
  return markdownToPlainPreview(value, INTERACTION_MESSAGE_MAX_LENGTH).trim();
}

function reactionItems(message: InteractionMessageDto, meId: string | null): ReactionBarItem[] {
  const grouped = new Map<string, ReactionBarItem>();
  for (const reaction of message.reactions ?? []) {
    const current = grouped.get(reaction.code) ?? {
      code: reaction.code,
      label: reaction.code,
      count: 0,
      reactedByMe: false,
    };
    current.count += 1;
    if (meId && reaction.user_id === meId) current.reactedByMe = true;
    grouped.set(reaction.code, current);
  }
  return [...grouped.values()];
}

export function InteractionRoomsPage({ getAccessToken, pathname, roomId, onNavigate }: Props) {
  const narrow = useNarrowWorkspace();
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
  const [pane, setPane] = useState<RoomPane>("chat");
  const [findOpen, setFindOpen] = useState(false);
  const [findQuery, setFindQuery] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [meId, setMeId] = useState<string | null>(null);
  const [meName, setMeName] = useState<string | null>(null);

  useEffect(() => {
    void fetchMeProfile(getAccessToken)
      .then((profile) => {
        setMeId(profile.id || null);
        setMeName(profile.name?.trim() || null);
      })
      .catch(() => undefined);
  }, [getAccessToken]);

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
    setPane("chat");
    setFindOpen(false);
    setFindQuery("");
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
    setPane("chat");
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

  async function saveEdit() {
    if (!roomId || !editingId) return;
    const content = editDraft.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
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
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = file.file_name;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setActionError(errorText(reason, "Não foi possível baixar o arquivo."));
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

  const authorName = useCallback(
    (authorUserId: string) => {
      if (meId && authorUserId === meId && meName) return meName;
      return "Nome indisponível";
    },
    [meId, meName],
  );

  const visibleRooms = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (rooms ?? []).filter((item) => {
      if (filter === "process" && !item.processo_id) return false;
      if (!needle) return true;
      const haystack = `${item.processo_nome} ${item.processo_codigo} ${item.last_message_preview ?? ""}`.toLowerCase();
      return haystack.includes(needle);
    });
  }, [filter, query, rooms]);

  const inboxItems = useMemo<RoomInboxListItem[]>(
    () =>
      visibleRooms.map((item) => ({
        id: item.id,
        title: item.processo_nome || item.processo_codigo || "Processo",
        preview: item.last_message_preview ? markdownToPlainPreview(item.last_message_preview) : null,
        metaLabel: item.last_message_at ? formatDateTime(item.last_message_at) : null,
        kindLabel: "Processo",
        unreadCount: item.unread_count ?? 0,
        mentioned: item.mentioned,
        selected: item.id === roomId,
      })),
    [roomId, visibleRooms],
  );

  const threadItems = useMemo<MessageThreadItem[]>(
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
          parentId: item.parent_id,
          mine: Boolean(meId && item.author_user_id === meId),
          deleted: removed,
          mentions: (item.mentions ?? []).map((mention) => ({
            kind: "user",
            id: mention.user_id,
            label: mention.label,
          })),
          belowBody: removed ? null : (
            <div className="tm-room-message-extra">
              {(item.attachments ?? []).map((file) => (
                <span key={file.id} className="tm-room-file-link">
                  <button type="button" onClick={() => void openFile(file)}>
                    {file.file_name}
                  </button>
                  {meId && file.uploaded_by_user_id === meId ? (
                    <button type="button" onClick={() => void removeFile(file)}>
                      Remover
                    </button>
                  ) : null}
                </span>
              ))}
              <ReactionBar
                classNames={REACTIONS}
                items={reactionItems(item, meId)}
                listAriaLabel="Reações"
                addAriaLabel="Reagir"
                onToggle={(code) => void react(item.id, code)}
                onAdd={(code) => void react(item.id, code)}
                emojiAdd={{ listAriaLabel: "Escolher reação" }}
              />
            </div>
          ),
        };
      }),
    [authorName, meId, messages],
  );

  const findResults = useMemo(() => {
    const needle = findQuery.trim().toLowerCase();
    if (needle.length < 2) return [];
    return (messages ?? [])
      .filter((item) => !item.deleted_at && item.content.toLowerCase().includes(needle))
      .map((item) => ({
        id: item.id,
        messageId: item.id,
        authorLabel: authorName(item.author_user_id),
        dateLabel: formatDateTime(item.created_at),
        bodyText: markdownToPlainPreview(item.content),
      }));
  }, [authorName, findQuery, messages]);

  const sharedItems = useMemo<RoomSharedItem[]>(
    () =>
      shared.map((file) => ({
        id: file.id,
        title: file.file_name,
        subtitle: file.content_type,
        whenLabel: file.created_at ? formatDateTime(file.created_at) : null,
        whoLabel: authorName(file.uploaded_by_user_id),
        ariaLabel: `Abrir ${file.file_name}`,
      })),
    [authorName, shared],
  );

  const replyTarget = (messages ?? []).find((item) => item.id === replyId) ?? null;
  const searchEmpty = query.trim().length > 0 && (rooms?.length ?? 0) > 0 && visibleRooms.length === 0;
  const initialLoading = rooms === null;

  const inbox = (
    <section className="tm-room-inbox-pane" aria-label="Conversas">
      <SectionCard
        classNames={SECTION}
        labels={SECTION_LABELS}
        title="Conversas"
        actions={
          <ActionButton type="button" variant="ghost" onClick={() => void refresh()} disabled={refreshing || initialLoading}>
            <RefreshCw size={16} aria-hidden="true" />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </ActionButton>
        }
      >
        <div className="tm-room-inbox-pane__filters">
          <CatalogSearchBar
            classNames={SEARCH}
            value={query}
            onChange={setQuery}
            placeholder="Buscar por título da sala"
            aria-label="Buscar por título da sala"
          />
          <ScopeChipBar
            classNames={CHIPS}
            aria-label="Filtros da caixa de entrada"
            chips={[
              { id: "all", label: "Todas", active: filter === "all", onSelect: () => setFilter("all") },
              { id: "unread", label: "Não lidas", active: filter === "unread", onSelect: () => setFilter("unread") },
              { id: "mentioned", label: "Menções", active: filter === "mentioned", onSelect: () => setFilter("mentioned") },
              { id: "process", label: "Processos", active: filter === "process", onSelect: () => setFilter("process") },
            ]}
          />
        </div>
      </SectionCard>
      {roomsError ? (
        <p className="tm-room-alert" role="alert">
          Não foi possível carregar as salas. {roomsError}
        </p>
      ) : null}
      {refreshing ? (
        <p className="tm-room-inbox-pane__refresh" role="status">
          Atualizando conversas…
        </p>
      ) : null}
      <RoomInboxPanel classNames={INBOX} aria-label="Salas de interação">
        {initialLoading ? (
          <LoadingActivityCard title="Carregando salas" description="Buscando as salas de interação já abertas." />
        ) : null}
        {!initialLoading && !roomsError && visibleRooms.length === 0 ? (
          <EmptyGuidance
            classNames={EMPTY}
            variant="panel"
            title={searchEmpty ? "Nenhuma sala com esse título" : "Nenhuma sala ainda"}
            message={
              searchEmpty
                ? "Tente outro nome ou código de processo."
                : filter === "unread"
                  ? "Nenhuma sala com mensagem nova."
                  : filter === "mentioned"
                    ? "Nenhuma menção nova."
                    : "Abra um processo para iniciar uma interação."
            }
          >
            {searchEmpty || filter === "unread" || filter === "mentioned" ? null : (
              <ActionButton type="button" onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.processes)}>
                Meus processos
              </ActionButton>
            )}
          </EmptyGuidance>
        ) : null}
        {!initialLoading && visibleRooms.length > 0 ? (
          <RoomInboxList
            classNames={INBOX}
            items={inboxItems}
            listAriaLabel="Salas de interação"
            emptyLabel="Nenhuma sala ainda"
            onSelect={(id) => onNavigate(buildInteractionRoomPath(id))}
            leading={(row) => <InitialsAvatar classNames={AVATAR} name={row.title} size="sm" />}
            subtitle={(row) => visibleRooms.find((item) => item.id === row.id)?.processo_codigo || "Processo"}
          />
        ) : null}
      </RoomInboxPanel>
    </section>
  );

  const thread = !roomId ? null : roomError && !room ? (
    <p className="tm-room-alert" role="alert">
      Não foi possível abrir a sala. {roomError}
    </p>
  ) : (
    <RoomConversationShell
      classNames={SHELL}
      dropClassNames={DROP}
      rootClassName="tm-room-thread"
      as="section"
      dropOverlayLabel="Solte o arquivo para anexar"
      accept={FILE_ACCEPT}
      onFiles={addFiles}
      header={
        <RoomHeader
          classNames={HEADER}
          title={room?.processo_nome || "Processo"}
          chips={room?.processo_codigo ? <span className={HEADER.chip}>{room.processo_codigo}</span> : null}
          titleActionLabel="Abrir processo"
          onTitleClick={room ? () => onNavigate(buildProcessoPath(room.processo_id)) : undefined}
          navAriaLabel="Conteúdo da sala"
          nav={
            <SegmentToggle
              classNames={SEGMENTS}
              ariaLabel="Conteúdo da sala"
              value={pane}
              onChange={setPane}
              options={[
                { value: "chat", label: "Conversa" },
                { value: "files", label: "Arquivos" },
              ]}
            />
          }
          leadingAction={
            narrow ? (
              <ActionButton
                type="button"
                variant="ghost"
                aria-label="Voltar para conversas"
                title="Voltar para conversas"
                onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.interactionRooms)}
              >
                <ArrowLeft size={16} aria-hidden="true" />
              </ActionButton>
            ) : undefined
          }
          actions={
            <ActionButton
              type="button"
              variant="ghost"
              aria-label="Buscar na conversa"
              aria-expanded={findOpen}
              onClick={() => setFindOpen((open) => !open)}
            >
              <Search size={16} aria-hidden="true" />
            </ActionButton>
          }
        />
      }
      sidePanel={
        findOpen ? (
          <RoomMessageFindPanel
            classNames={FIND}
            labels={{
              title: "Buscar na conversa",
              closeAriaLabel: "Fechar busca",
              placeholder: "Buscar nas mensagens carregadas",
              clear: "Limpar",
              empty: "Nenhuma mensagem com esse texto.",
              loading: "Buscando…",
            }}
            query={findQuery}
            onQueryChange={setFindQuery}
            onClear={() => setFindQuery("")}
            onClose={() => setFindOpen(false)}
            results={findResults}
            onSelectResult={(messageId) => {
              setPane("chat");
              document.querySelector(`[data-message-id="${CSS.escape(messageId)}"]`)?.scrollIntoView({
                block: "center",
              });
            }}
          />
        ) : undefined
      }
      main={
        messages === null && !messagesError ? (
          <LoadingActivityCard title="Carregando a sala…" description="Buscando a conversa deste processo." />
        ) : pane === "files" ? (
          <RoomSharedItemList
            classNames={SHARED}
            items={sharedItems}
            listAriaLabel="Arquivos da sala"
            onOpen={(id) => {
              const file = shared.find((item) => item.id === id);
              if (file) void openFile(file);
            }}
          >
            <EmptyGuidance
              classNames={EMPTY}
              variant="panel"
              title="Nenhum arquivo ainda"
              message="Anexe um arquivo na conversa para ele aparecer aqui."
            />
          </RoomSharedItemList>
        ) : (
          <RoomConversationChatColumn
            classNames={SHELL}
            dock={
              <div aria-busy={sending || undefined}>
                {sendError ? (
                  <p className="tm-room-alert" role="alert">
                    {sendError}
                  </p>
                ) : null}
                <MentionComposer
                  key={roomId}
                  classNames={COMPOSER}
                  labels={COMPOSER_LABELS}
                  value={draft}
                  onChange={setDraft}
                  onSubmit={(markdown) => void send(markdown)}
                  submitting={sending}
                  disabled={sending}
                  showAttach={true}
                  pendingAttachments={pending}
                  onFilesSelected={addFiles}
                  onRemovePendingAttachment={(id) => setPending((current) => current.filter((item) => item.id !== id))}
                  mentionHits={mentionHits}
                  onMentionQueryChange={(next) => {
                    if (!next?.trim()) {
                      setMentionHits([]);
                      return;
                    }
                    void searchDirectoryUsers(next.trim(), 8, undefined, getAccessToken)
                      .then((users) =>
                        setMentionHits(
                          users.map((user) => ({
                            id: user.id,
                            kind: "user",
                            label: user.name,
                            subtitle: user.email,
                            avatarName: user.name,
                          })),
                        ),
                      )
                      .catch(() => setMentionHits([]));
                  }}
                  onMentionInserted={(hit) => {
                    const label = hit.label.replace(/^@/, "").trim();
                    if (!label) return;
                    mentionsRef.current = [
                      ...mentionsRef.current.filter((item) => item.user_id !== hit.id),
                      { user_id: hit.id, label },
                    ];
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
                />
              </div>
            }
          >
            {refreshing ? (
              <p className="tm-room-thread__refresh" role="status">
                Atualizando mensagens…
              </p>
            ) : null}
            {messagesError ? (
              <p className="tm-room-alert" role="alert">
                Não foi possível carregar as mensagens. {messagesError}
              </p>
            ) : null}
            {actionError ? (
              <p className="tm-room-alert" role="alert">
                {actionError}
              </p>
            ) : null}
            {hasMore ? <p>Mostrando as mensagens mais recentes.</p> : null}
            <MessageThread
              classNames={THREAD}
              messages={threadItems}
              listAriaLabel="Mensagens da sala"
              emptyLabel="Nenhuma mensagem ainda"
              editingId={editingId}
              renderEditSlot={() => (
                <form
                  className="tm-room-edit"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void saveEdit();
                  }}
                >
                  <textarea
                    value={editDraft}
                    maxLength={INTERACTION_MESSAGE_MAX_LENGTH}
                    aria-label="Editar mensagem"
                    onChange={(event) => setEditDraft(event.target.value)}
                  />
                  <span>
                    <ActionButton type="submit">Salvar</ActionButton>
                    <ActionButton type="button" variant="ghost" onClick={() => setEditingId(null)}>
                      Cancelar
                    </ActionButton>
                  </span>
                </form>
              )}
              resolveActions={(row) => {
                const source = (messages ?? []).find((item) => item.id === row.id);
                if (!source || source.deleted_at) return [];
                const mine = Boolean(meId && source.author_user_id === meId);
                return [
                  {
                    id: "reply",
                    label: "Responder",
                    icon: <Reply size={16} aria-hidden="true" />,
                    onClick: () => {
                      setReplyId(source.id);
                      setEditingId(null);
                    },
                  },
                  {
                    id: "pin",
                    label: source.pinned ? "Desafixar" : "Fixar",
                    icon: <Pin size={16} aria-hidden="true" />,
                    onClick: () => void togglePin(source),
                  },
                  ...(mine
                    ? [
                        {
                          id: "edit",
                          label: "Editar",
                          icon: <Pencil size={16} aria-hidden="true" />,
                          onClick: () => {
                            setEditingId(source.id);
                            setEditDraft(source.content);
                          },
                        },
                        {
                          id: "delete",
                          label: "Remover",
                          danger: true,
                          icon: <Trash2 size={16} aria-hidden="true" />,
                          onClick: () => void removeMessage(source.id),
                        },
                      ]
                    : []),
                ];
              }}
              emptyContent={
                <EmptyGuidance
                  classNames={EMPTY}
                  variant="canvas"
                  title="Nenhuma mensagem ainda"
                  message="Escreva a primeira mensagem nesta sala."
                  icon={<MessageSquare aria-hidden="true" />}
                />
              }
            />
          </RoomConversationChatColumn>
        )
      }
    />
  );

  return (
    <TransformometroShell>
      <PortalTopBar currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.interactionRooms} onNavigate={onNavigate} />
      <div className="tm-room-workspace">
        <div className="tm-room-workspace__grid">
          {narrow ? (
            roomId ? (
              thread
            ) : (
              inbox
            )
          ) : roomId ? (
            <ResizableColumns
              classNames={COLUMNS}
              left={inbox}
              right={thread}
              labels={{
                separatorAriaLabel: "Redimensionar lista de salas",
                collapseAriaLabel: "Recolher lista de salas",
                expandAriaLabel: "Mostrar lista de salas",
              }}
            />
          ) : (
            inbox
          )}
        </div>
      </div>
    </TransformometroShell>
  );
}
