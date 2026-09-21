import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, MessageSquare, RefreshCw } from "lucide-react";
import {
  ActionButton,
  CatalogSearchBar,
  EmptyGuidance,
  InitialsAvatar,
  MentionComposer,
  MessageThread,
  ResizableColumns,
  RoomConversationChatColumn,
  RoomHeader,
  RoomInboxList,
  RoomInboxPanel,
  ScopeChipBar,
  SectionCard,
  catalogSearchBarBemClasses,
  emptyGuidanceBemClasses,
  initialsAvatarBemClasses,
  markdownToPlainPreview,
  mentionComposerBemClasses,
  messageThreadBemClasses,
  resizableColumnsBemClasses,
  roomConversationShellBemClasses,
  roomHeaderBemClasses,
  roomInboxListBemClasses,
  scopeChipBarBemClasses,
  sectionCardPacBemClasses,
  type MessageThreadItem,
  type RoomInboxListItem,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PortalTopBar } from "../../components/TransformometroNav";
import { TRANSFORMOMETRO_ROUTES, buildInteractionRoomPath } from "../../constants/routes";
import { fetchMeProfile } from "../../data/api/meApi";
import {
  INTERACTION_MESSAGE_MAX_LENGTH,
  getInteractionRoom,
  listInteractionMessages,
  listInteractionRooms,
  postInteractionMessage,
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

type InboxFilter = "all" | "process";

const SECTION = sectionCardPacBemClasses("ds");
const SECTION_LABELS = { titleHelpAriaLabel: (title: string) => title };
const SEARCH = catalogSearchBarBemClasses("ds");
const CHIPS = scopeChipBarBemClasses("ds");
const INBOX = roomInboxListBemClasses("ds");
const AVATAR = initialsAvatarBemClasses("ds");
const HEADER = roomHeaderBemClasses("ds");
const THREAD = messageThreadBemClasses("ds");
const SHELL = roomConversationShellBemClasses("ds");
const COLUMNS = resizableColumnsBemClasses("ds");
const EMPTY = emptyGuidanceBemClasses("ds");
const COMPOSER = mentionComposerBemClasses("ds");

const COMPOSER_LABELS = {
  placeholder: "Escreva uma mensagem…",
  sendAriaLabel: "Enviar",
  attachAriaLabel: "Anexar arquivo",
  mentionListAriaLabel: "Pessoas",
  mentionEmptyLabel: "Nenhuma pessoa para mencionar",
  formatToggleAriaLabel: "Formatação",
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

export function InteractionRoomsPage({ getAccessToken, pathname, roomId, onNavigate }: Props) {
  const narrow = useNarrowWorkspace();
  const [rooms, setRooms] = useState<InteractionRoomDto[] | null>(null);
  const [roomsError, setRoomsError] = useState<string | null>(null);
  const [room, setRoom] = useState<InteractionRoomDto | null>(null);
  const [roomError, setRoomError] = useState<string | null>(null);
  const [messages, setMessages] = useState<InteractionMessageDto[] | null>(null);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<InboxFilter>("all");
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
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
    const page = await listInteractionRooms(getAccessToken);
    setRooms(page.items);
    setRoomsError(null);
  }, [getAccessToken]);

  const loadThread = useCallback(async () => {
    if (!roomId) {
      setRoom(null);
      setRoomError(null);
      setMessages(null);
      setMessagesError(null);
      setHasMore(false);
      return;
    }
    const [nextRoom, nextMessages] = await Promise.all([
      getInteractionRoom(roomId, getAccessToken),
      listInteractionMessages(roomId, getAccessToken),
    ]);
    setRoom(nextRoom);
    setRoomError(null);
    setMessages(nextMessages.items);
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
    setSendError(null);
    setRoom(null);
    setMessages(null);
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

  async function send(markdown: string) {
    if (!roomId || sending) return;
    const content = markdown.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
    if (!plainMessage(content)) {
      setSendError("A mensagem não pode ficar em branco.");
      return;
    }
    if (content.length > INTERACTION_MESSAGE_MAX_LENGTH) {
      setSendError(`A mensagem pode ter no máximo ${INTERACTION_MESSAGE_MAX_LENGTH} caracteres.`);
      return;
    }
    setSending(true);
    setSendError(null);
    try {
      const saved = await postInteractionMessage(roomId, content, getAccessToken);
      if (!saved.id || saved.room_id !== roomId || saved.content !== content) {
        throw new Error("O envio não confirmou a mensagem.");
      }
      setMessages((current) => [...(current ?? []), saved]);
      setDraft("");
      setMessagesError(null);
      void loadRooms().catch(() => undefined);
    } catch (reason) {
      setSendError(errorText(reason, "Não foi possível enviar a mensagem."));
    } finally {
      setSending(false);
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
        preview: item.last_message_preview
          ? markdownToPlainPreview(item.last_message_preview)
          : null,
        metaLabel: item.last_message_at ? formatDateTime(item.last_message_at) : null,
        kindLabel: "Processo",
        selected: item.id === roomId,
      })),
    [roomId, visibleRooms],
  );

  const threadItems = useMemo<MessageThreadItem[]>(
    () =>
      (messages ?? []).map((item) => ({
        id: item.id,
        kind: "text",
        bodyText: item.content,
        createdAtLabel: formatDateTime(item.created_at),
        authorName: authorName(item.author_user_id),
        authorUserId: item.author_user_id,
        mine: Boolean(meId && item.author_user_id === meId),
      })),
    [authorName, meId, messages],
  );

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
              {
                id: "process",
                label: "Processos",
                active: filter === "process",
                onSelect: () => setFilter("process"),
              },
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
                : "Abra um processo para iniciar uma interação."
            }
          >
            {searchEmpty ? null : (
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
            leading={(row) => (
              <InitialsAvatar classNames={AVATAR} name={row.title} size="sm" />
            )}
            subtitle={(row) =>
              visibleRooms.find((item) => item.id === row.id)?.processo_codigo || "Processo"
            }
          />
        ) : null}
      </RoomInboxPanel>
    </section>
  );

  const thread = !roomId ? null : (
    <section className={`tm-room-thread ${SHELL.root}`} aria-label="Conversa">
      {roomError && !room ? (
        <p className="tm-room-alert" role="alert">
          Não foi possível abrir a sala. {roomError}
        </p>
      ) : (
        <>
          <div className={SHELL.header}>
            <RoomHeader
              classNames={HEADER}
              title={room?.processo_nome || "Processo"}
              chips={
                room?.processo_codigo ? (
                  <span className={HEADER.chip}>{room.processo_codigo}</span>
                ) : null
              }
              titleActionLabel="Abrir processo"
              onTitleClick={room ? () => onNavigate(buildProcessoPath(room.processo_id)) : undefined}
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
            />
          </div>
          <div className={SHELL.body}>
            <div className={SHELL.main}>
              {messages === null && !messagesError ? (
                <LoadingActivityCard
                  title="Carregando a sala…"
                  description="Buscando a conversa deste processo."
                />
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
                        showAttach={false}
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
                  {hasMore ? <p>Mostrando as mensagens mais recentes.</p> : null}
                  <MessageThread
                    classNames={THREAD}
                    messages={threadItems}
                    listAriaLabel="Mensagens da sala"
                    emptyLabel="Nenhuma mensagem ainda"
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
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );

  return (
    <TransformometroShell>
      <PortalTopBar
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.interactionRooms}
        onNavigate={onNavigate}
      />
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
