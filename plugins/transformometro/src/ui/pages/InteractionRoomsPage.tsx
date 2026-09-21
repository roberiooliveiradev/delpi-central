import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  EmptyState,
  MessageThread,
  RoomConversationChatColumn,
  RoomHeader,
  RoomInboxList,
  emptyStatePanelBemClasses,
  messageThreadBemClasses,
  roomConversationShellBemClasses,
  roomHeaderBemClasses,
  roomInboxListBemClasses,
  type MessageThreadItem,
  type RoomInboxListItem,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_PAGE_COPY } from "../../constants/portalExperience";
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

const INBOX = roomInboxListBemClasses("ds");
const HEADER = roomHeaderBemClasses("ds");
const THREAD = messageThreadBemClasses("ds");
const CHAT = roomConversationShellBemClasses("ds");
const EMPTY = emptyStatePanelBemClasses("ds");

function errorText(reason: unknown, fallback: string): string {
  return reason instanceof Error && reason.message ? reason.message : fallback;
}

export function InteractionRoomsPage({ getAccessToken, pathname, roomId, onNavigate }: Props) {
  const copy = PORTAL_PAGE_COPY.interactionRooms;
  const [rooms, setRooms] = useState<InteractionRoomDto[] | null>(null);
  const [roomsError, setRoomsError] = useState<string | null>(null);
  const [room, setRoom] = useState<InteractionRoomDto | null>(null);
  const [roomError, setRoomError] = useState<string | null>(null);
  const [messages, setMessages] = useState<InteractionMessageDto[] | null>(null);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
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

  async function send() {
    if (!roomId || sending) return;
    const content = draft.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
    if (!content) {
      setSendError("A mensagem não pode ficar em branco.");
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

  const inboxItems = useMemo<RoomInboxListItem[]>(() => {
    const source = rooms ?? [];
    return source.map((item) => ({
      id: item.id,
      title: item.processo_nome || item.processo_codigo || "Processo",
      preview: item.last_message_preview,
      metaLabel: item.last_message_at ? formatDateTime(item.last_message_at) : null,
      kindLabel: item.processo_codigo || "Processo",
      selected: item.id === roomId,
    }));
  }, [roomId, rooms]);

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

  const initialLoading = rooms === null;

  return (
    <TransformometroShell>
      <PageHeader
        eyebrow={copy.eyebrow}
        title={copy.title}
        subtitle={copy.description}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.interactionRooms}
        onNavigate={onNavigate}
        onRefresh={initialLoading ? undefined : () => void refresh()}
        refreshing={refreshing}
      />
      {initialLoading ? (
        <LoadingActivityCard
          title="Carregando salas"
          description="Buscando as salas de interação já abertas."
        />
      ) : (
        <div
          className={roomId ? "tm-interaction-room tm-interaction-room--thread" : "tm-interaction-room"}
          aria-busy={refreshing || undefined}
        >
          <section className="tm-interaction-room__inbox" aria-label="Contextos">
            {roomsError ? (
              <p className="tm-interaction-room__alert" role="alert">
                Não foi possível carregar as salas. {roomsError}
              </p>
            ) : null}
            {!roomsError && (rooms?.length ?? 0) === 0 ? (
              <EmptyState
                classNames={EMPTY}
                title="Nenhuma sala ainda"
                defaultTitle="Nenhuma sala ainda"
                defaultMessage="Abra um processo para iniciar uma interação."
              >
                <ActionButton type="button" onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.processes)}>
                  Meus processos
                </ActionButton>
              </EmptyState>
            ) : (
              <RoomInboxList
                classNames={INBOX}
                items={inboxItems}
                listAriaLabel="Processos com sala"
                emptyLabel="Nenhuma sala ainda."
                onSelect={(id) => onNavigate(buildInteractionRoomPath(id))}
              />
            )}
          </section>
          <section className="tm-interaction-room__thread" aria-label="Conversa">
            {!roomId ? (
              <EmptyState
                classNames={EMPTY}
                title="Escolha um processo"
                defaultTitle="Escolha um processo"
                defaultMessage="Selecione uma sala na lista para ler e escrever."
              />
            ) : roomError && !room ? (
              <p className="tm-interaction-room__alert" role="alert">
                Não foi possível abrir a sala. {roomError}
              </p>
            ) : (
              <>
                <RoomHeader
                  classNames={HEADER}
                  title={room?.processo_nome || "Processo"}
                  subtitle={room?.processo_codigo || "Processo"}
                  titleActionLabel="Abrir processo"
                  onTitleClick={
                    room ? () => onNavigate(buildProcessoPath(room.processo_id)) : undefined
                  }
                  leadingAction={
                    <ActionButton
                      type="button"
                      variant="ghost"
                      onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.interactionRooms)}
                    >
                      Contextos
                    </ActionButton>
                  }
                />
                {messages === null && !messagesError ? (
                  <LoadingActivityCard
                    title="Carregando mensagens"
                    description="Buscando a conversa deste processo."
                  />
                ) : (
                  <RoomConversationChatColumn
                    classNames={CHAT}
                    dock={
                      <form
                        className="tm-interaction-room__composer"
                        aria-busy={sending || undefined}
                        onSubmit={(event) => {
                          event.preventDefault();
                          void send();
                        }}
                      >
                        <label htmlFor="tm-interaction-message">Mensagem</label>
                        <textarea
                          id="tm-interaction-message"
                          value={draft}
                          maxLength={INTERACTION_MESSAGE_MAX_LENGTH}
                          disabled={sending}
                          aria-invalid={sendError ? true : undefined}
                          onChange={(event) => setDraft(event.target.value)}
                        />
                        {sendError ? (
                          <p className="tm-interaction-room__alert" role="alert">
                            {sendError}
                          </p>
                        ) : null}
                        <div className="tm-interaction-room__composer-actions">
                          <ActionButton type="submit" disabled={sending}>
                            {sending ? "Enviando…" : "Enviar"}
                          </ActionButton>
                        </div>
                      </form>
                    }
                  >
                    {messagesError ? (
                      <p className="tm-interaction-room__alert" role="alert">
                        Não foi possível carregar as mensagens. {messagesError}
                      </p>
                    ) : null}
                    {hasMore ? <p>Mostrando as mensagens mais recentes.</p> : null}
                    <MessageThread
                      classNames={THREAD}
                      messages={threadItems}
                      listAriaLabel="Mensagens da sala"
                      emptyLabel="Nenhuma interação ainda."
                      emptyContent={
                        <EmptyState
                          classNames={EMPTY}
                          title="Nenhuma interação ainda."
                          defaultTitle="Nenhuma interação ainda."
                          defaultMessage="Escreva a primeira mensagem deste processo."
                        />
                      }
                      renderBody={(message) => (
                        <span className="tm-interaction-room__body">{message.bodyText}</span>
                      )}
                    />
                  </RoomConversationChatColumn>
                )}
              </>
            )}
          </section>
        </div>
      )}
    </TransformometroShell>
  );
}
