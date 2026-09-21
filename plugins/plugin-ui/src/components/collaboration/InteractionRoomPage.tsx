/**
 * Canonical interaction room canvas.
 * Hosts pass data and commands. This module does not fetch, authorize, or know a portal domain.
 */

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowLeft, Copy, Files, MessageSquare, PanelRight, Pencil, Pin, RefreshCw, Reply, Search, Trash2 } from "lucide-react";

import { ActionButton } from "../actions/ActionButton";
import { EmptyGuidance, emptyGuidanceBemClasses } from "../feedback/EmptyGuidance";
import { ScopeChipBar, scopeChipBarBemClasses, type ScopeChip } from "../feedback/ScopeChipBar";
import { TextField, textFieldBemClasses } from "../forms/TextField";
import { SegmentToggle, segmentToggleBemClasses } from "../forms/SegmentToggle";
import { CatalogSearchBar, catalogSearchBarBemClasses } from "../layout/CatalogSearchBar";
import { InitialsAvatar, initialsAvatarBemClasses } from "../layout/InitialsAvatar";
import { ResizableColumns, resizableColumnsBemClasses } from "../layout/ResizableColumns";
import { SectionCard, sectionCardPacBemClasses } from "../layout/SectionCard";
import { UnderlineNav, underlineNavBemClasses } from "../layout/UnderlineNav";
import { delpiUiClass } from "../../utils/delpiUiClass";
import type { AvatarStackItem } from "../layout/AvatarStack";
import {
  MentionComposer,
  mentionComposerBemClasses,
  type MentionComposerLabels,
  type MentionComposerPendingAttachment,
  type MentionComposerReplyTo,
  type MentionMenuHit,
} from "./MentionComposer";
import {
  MessageThread,
  messageThreadBemClasses,
  type MessageThreadItem,
} from "./MessageThread";
import { ReactionBar, reactionBarBemClasses, type ReactionBarItem } from "./ReactionBar";
import {
  RoomContextPanel,
  roomContextPanelBemClasses,
  type RoomContextEntityField,
  type RoomContextPanelLabels,
  type RoomContextPanelPin,
} from "./RoomContextPanel";
import {
  conversationFileDropLayerBemClasses,
} from "./ConversationFileDropLayer";
import {
  RoomConversationChatColumn,
  RoomConversationShell,
  roomConversationShellBemClasses,
} from "./RoomConversationShell";
import { RoomHeader, roomHeaderBemClasses } from "./RoomHeader";
import {
  RoomInboxList,
  RoomInboxPanel,
  roomInboxListBemClasses,
  type RoomInboxListItem,
} from "./RoomInboxList";
import {
  RoomMessageFindPanel,
  roomMessageFindPanelBemClasses,
  type RoomMessageFindPanelLabels,
  type RoomMessageFindResult,
} from "./RoomMessageFindPanel";
import {
  RoomSharedItemList,
  roomSharedItemListBemClasses,
  type RoomSharedItem,
} from "./RoomSharedItemList";
import { RoomSidePanel, roomSidePanelBemClasses } from "./RoomSidePanel";
import { markdownToPlainPreview } from "./messageThreadMarkdown";

export type InteractionRoomPane = "chat" | "shared";
export type InteractionRoomSide = "find" | "context" | null;
export type InteractionRoomSharedKind = "recent" | "file" | "link";

export type InteractionRoomAttachment = {
  id: string;
  fileName: string;
  removable?: boolean;
};

export type InteractionRoomMessage = MessageThreadItem & {
  pinned?: boolean;
  reactions?: readonly ReactionBarItem[];
  files?: readonly InteractionRoomAttachment[];
};

export type InteractionRoomSharedItem = RoomSharedItem & {
  kind: "file" | "link";
  href?: string | null;
};

export type InteractionRoomPageLabels = {
  inboxTitle: string;
  refresh: string;
  refreshing: string;
  searchPlaceholder: string;
  searchAriaLabel: string;
  filtersAriaLabel: string;
  inboxListAriaLabel: string;
  inboxEmptyTitle: string;
  inboxEmptyMessage: string;
  inboxSearchEmptyTitle: string;
  inboxSearchEmptyMessage: string;
  backAriaLabel: string;
  roomViewNavAriaLabel: string;
  roomViewChat: string;
  roomViewShared: string;
  findAriaLabel: string;
  contextAriaLabel: string;
  contextCloseAriaLabel: string;
  contextTitle: string;
  copyLinkAriaLabel: string;
  resizeSeparator: string;
  collapseInbox: string;
  expandInbox: string;
  threadAriaLabel: string;
  messagesAriaLabel: string;
  emptyThreadTitle: string;
  emptyThreadMessage: string;
  loadingRoomsTitle: string;
  loadingRoomsMessage: string;
  loadingThreadTitle: string;
  loadingThreadMessage: string;
  hasMore: string;
  dropOverlay: string;
  reply: string;
  pin: string;
  unpin: string;
  edit: string;
  delete: string;
  removeFile: string;
  reactionsList: string;
  react: string;
  chooseReaction: string;
  sharedRecent: string;
  sharedFiles: string;
  sharedLinks: string;
  sharedFilterPlaceholder: string;
  sharedEmptyTitle: string;
  sharedEmptyMessage: string;
  sharedListAriaLabel: string;
  composer: MentionComposerLabels;
  find: RoomMessageFindPanelLabels;
  context: RoomContextPanelLabels;
};

export const INTERACTION_ROOM_PAGE_LABELS_PT: InteractionRoomPageLabels = {
  inboxTitle: "Conversas",
  refresh: "Atualizar",
  refreshing: "Atualizando…",
  searchPlaceholder: "Buscar por título da sala",
  searchAriaLabel: "Buscar por título da sala",
  filtersAriaLabel: "Filtros da caixa de entrada",
  inboxListAriaLabel: "Salas de interação",
  inboxEmptyTitle: "Nenhuma sala ainda",
  inboxEmptyMessage: "Abra um registro para iniciar uma interação.",
  inboxSearchEmptyTitle: "Nenhuma sala com esse título",
  inboxSearchEmptyMessage: "Tente outro nome.",
  backAriaLabel: "Voltar para conversas",
  roomViewNavAriaLabel: "Conteúdo da sala",
  roomViewChat: "Conversa",
  roomViewShared: "Arquivos e links",
  findAriaLabel: "Buscar na conversa",
  contextAriaLabel: "Neste chat",
  contextCloseAriaLabel: "Fechar painel da sala",
  contextTitle: "Neste chat",
  copyLinkAriaLabel: "Copiar link da sala",
  resizeSeparator: "Redimensionar lista de salas",
  collapseInbox: "Recolher lista de salas",
  expandInbox: "Mostrar lista de salas",
  threadAriaLabel: "Conversa",
  messagesAriaLabel: "Mensagens da sala",
  emptyThreadTitle: "Nenhuma mensagem ainda",
  emptyThreadMessage: "Escreva a primeira mensagem nesta sala.",
  loadingRoomsTitle: "Carregando salas",
  loadingRoomsMessage: "Buscando as salas já abertas.",
  loadingThreadTitle: "Carregando a sala…",
  loadingThreadMessage: "Buscando a conversa.",
  hasMore: "Mostrando as mensagens mais recentes.",
  dropOverlay: "Solte o arquivo para anexar",
  reply: "Responder",
  pin: "Fixar",
  unpin: "Desafixar",
  edit: "Editar",
  delete: "Remover",
  removeFile: "Remover",
  reactionsList: "Reações",
  react: "Reagir",
  chooseReaction: "Escolher reação",
  sharedRecent: "Recentes",
  sharedFiles: "Arquivos",
  sharedLinks: "Links",
  sharedFilterPlaceholder: "Filtrar por palavra-chave",
  sharedEmptyTitle: "Nada compartilhado ainda",
  sharedEmptyMessage: "Arquivos e links das mensagens aparecem aqui. Anexe pelo chat.",
  sharedListAriaLabel: "Itens compartilhados da sala",
  composer: {
    placeholder: "Escreva uma mensagem… Use @ para mencionar.",
    sendAriaLabel: "Enviar",
    attachAriaLabel: "Anexar arquivo",
    mentionListAriaLabel: "Pessoas",
    mentionEmptyLabel: "Nenhuma pessoa para mencionar",
    formatToggleAriaLabel: "Formatação",
    replyCancelAriaLabel: "Cancelar resposta",
  },
  find: {
    title: "Localizar no chat",
    closeAriaLabel: "Fechar busca",
    placeholder: "Buscar mensagens…",
    clear: "Limpar",
    empty: "Nenhuma mensagem com esse texto.",
    loading: "Buscando…",
  },
  context: {
    about: "Sobre",
    participants: "Quem falou",
    pins: "Fixadas",
    pinsEmpty: "Nenhuma mensagem fixada",
    membersEmpty: "Ninguém falou nesta sala ainda.",
    openEntity: "Abrir",
  },
};

export type InteractionRoomPageProps = {
  prefix?: string;
  labels?: InteractionRoomPageLabels;
  inboxQuery: string;
  onInboxQueryChange: (value: string) => void;
  chips: readonly ScopeChip[];
  rooms: readonly RoomInboxListItem[];
  roomsLoading?: boolean;
  roomsRefreshing?: boolean;
  roomsError?: string | null;
  inboxEmptyTitle?: string;
  inboxEmptyMessage?: string;
  inboxEmptyAction?: ReactNode;
  onRefresh: () => void;
  onSelectRoom: (id: string) => void;
  inboxSubtitle?: (item: RoomInboxListItem) => ReactNode;
  room: {
    id: string;
    title: string;
    chips?: ReactNode;
    titleActionLabel?: string;
    onTitleClick?: () => void;
    participants?: readonly AvatarStackItem[];
    participantsAriaLabel?: string;
  } | null;
  onBack?: () => void;
  messages: readonly InteractionRoomMessage[];
  messagesLoading?: boolean;
  messagesError?: string | null;
  composerError?: string | null;
  actionError?: string | null;
  hasMore?: boolean;
  editingId?: string | null;
  renderEditSlot?: (message: InteractionRoomMessage) => ReactNode;
  draft: string;
  onDraftChange: (value: string) => void;
  onSubmit: (markdown: string) => void;
  submitting?: boolean;
  pendingAttachments?: readonly MentionComposerPendingAttachment[];
  onFiles: (files: File[]) => void;
  onRemovePendingAttachment?: (id: string) => void;
  accept: string;
  mentionHits?: readonly MentionMenuHit[];
  onMentionQueryChange?: (query: string | null) => void;
  onMentionInserted?: (hit: MentionMenuHit, token: string) => void;
  replyTo?: MentionComposerReplyTo | null;
  onCancelReply?: () => void;
  onReply?: (messageId: string) => void;
  onTogglePin?: (message: InteractionRoomMessage) => void;
  onEdit?: (message: InteractionRoomMessage) => void;
  onDelete?: (messageId: string) => void;
  onToggleReaction?: (messageId: string, code: string) => void;
  onOpenAttachment?: (attachmentId: string) => void;
  onRemoveAttachment?: (attachmentId: string) => void;
  sharedItems: readonly InteractionRoomSharedItem[];
  onOpenShared: (item: InteractionRoomSharedItem) => void;
  entityPrimary?: string | null;
  entityFields?: readonly RoomContextEntityField[];
  entityHref?: string | null;
  onOpenEntity?: () => void;
  onCopyLink?: () => void;
  headerMenu?: ReactNode;
  threadStatus?: ReactNode;
};

function useNarrowRoom() {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const media = window.matchMedia("(max-width: 900px)");
    const apply = () => setNarrow(media.matches);
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, []);
  return narrow;
}

export function InteractionRoomPage({
  prefix = "ds",
  labels = INTERACTION_ROOM_PAGE_LABELS_PT,
  inboxQuery,
  onInboxQueryChange,
  chips,
  rooms,
  roomsLoading = false,
  roomsRefreshing = false,
  roomsError = null,
  inboxEmptyTitle,
  inboxEmptyMessage,
  inboxEmptyAction,
  onRefresh,
  onSelectRoom,
  inboxSubtitle,
  room,
  onBack,
  messages,
  messagesLoading = false,
  messagesError = null,
  composerError = null,
  actionError = null,
  hasMore = false,
  editingId = null,
  renderEditSlot,
  draft,
  onDraftChange,
  onSubmit,
  submitting = false,
  pendingAttachments,
  onFiles,
  onRemovePendingAttachment,
  accept,
  mentionHits,
  onMentionQueryChange,
  onMentionInserted,
  replyTo = null,
  onCancelReply,
  onReply,
  onTogglePin,
  onEdit,
  onDelete,
  onToggleReaction,
  onOpenAttachment,
  onRemoveAttachment,
  sharedItems,
  onOpenShared,
  entityPrimary,
  entityFields,
  entityHref,
  onOpenEntity,
  onCopyLink,
  headerMenu,
  threadStatus,
}: InteractionRoomPageProps) {
  const narrow = useNarrowRoom();
  const [pane, setPane] = useState<InteractionRoomPane>("chat");
  const [side, setSide] = useState<InteractionRoomSide>(null);
  const [sharedKind, setSharedKind] = useState<InteractionRoomSharedKind>("recent");
  const [sharedFilter, setSharedFilter] = useState("");
  const [findQuery, setFindQuery] = useState("");

  useEffect(() => {
    setPane("chat");
    setSide(null);
    setSharedKind("recent");
    setSharedFilter("");
    setFindQuery("");
  }, [room?.id]);

  const section = sectionCardPacBemClasses(prefix);
  const search = catalogSearchBarBemClasses(prefix);
  const scope = scopeChipBarBemClasses(prefix);
  const inbox = roomInboxListBemClasses(prefix);
  const avatar = initialsAvatarBemClasses(prefix);
  const header = roomHeaderBemClasses(prefix);
  const thread = messageThreadBemClasses(prefix);
  const shell = roomConversationShellBemClasses(prefix);
  const drop = conversationFileDropLayerBemClasses(prefix);
  const columns = resizableColumnsBemClasses(prefix);
  const empty = emptyGuidanceBemClasses(prefix);
  const composer = mentionComposerBemClasses(prefix);
  const reactions = reactionBarBemClasses(prefix);
  const shared = roomSharedItemListBemClasses(prefix);
  const find = roomMessageFindPanelBemClasses(prefix);
  const context = roomContextPanelBemClasses(prefix);
  const sidePanel = roomSidePanelBemClasses(prefix);
  const segments = segmentToggleBemClasses(prefix);
  const nav = underlineNavBemClasses(prefix);
  const field = textFieldBemClasses(prefix);
  const root = delpiUiClass(`${prefix}-interaction-room`, "delpi-ui-interaction-room");

  const searchEmpty = inboxQuery.trim().length > 0 && rooms.length === 0 && !roomsLoading;
  const visibleShared = useMemo(() => {
    const needle = sharedFilter.trim().toLowerCase();
    return sharedItems.filter((item) => {
      if (sharedKind === "file" && item.kind !== "file") return false;
      if (sharedKind === "link" && item.kind !== "link") return false;
      if (!needle) return true;
      return `${item.title} ${item.subtitle ?? ""}`.toLowerCase().includes(needle);
    });
  }, [sharedFilter, sharedItems, sharedKind]);

  const findResults = useMemo<RoomMessageFindResult[]>(() => {
    const needle = findQuery.trim().toLowerCase();
    if (needle.length < 2) return [];
    return messages
      .filter((item) => !item.deleted && item.bodyText.toLowerCase().includes(needle))
      .map((item) => ({
        id: item.id,
        messageId: item.id,
        authorLabel: item.authorName || "",
        dateLabel: item.createdAtLabel,
        bodyText: markdownToPlainPreview(item.bodyText),
      }));
  }, [findQuery, messages]);

  function focusMessage(messageId: string) {
    setPane("chat");
    window.requestAnimationFrame(() => {
      document.querySelector(`[data-message-id="${CSS.escape(messageId)}"]`)?.scrollIntoView({
        block: "center",
      });
    });
  }

  const inboxPane = (
    <section className={`${root}__inbox`} aria-label={labels.inboxTitle}>
      <SectionCard
        classNames={section}
        labels={{ titleHelpAriaLabel: (title) => title }}
        title={labels.inboxTitle}
        actions={
          <ActionButton type="button" variant="ghost" onClick={onRefresh} disabled={roomsRefreshing || roomsLoading}>
            <RefreshCw size={16} aria-hidden="true" />
            {roomsRefreshing ? labels.refreshing : labels.refresh}
          </ActionButton>
        }
      >
        <div className={`${root}__filters`}>
          <CatalogSearchBar
            classNames={search}
            value={inboxQuery}
            onChange={onInboxQueryChange}
            placeholder={labels.searchPlaceholder}
            aria-label={labels.searchAriaLabel}
          />
          <ScopeChipBar classNames={scope} aria-label={labels.filtersAriaLabel} chips={[...chips]} />
        </div>
      </SectionCard>
      {roomsError ? (
        <p className={`${root}__alert`} role="alert">
          {roomsError}
        </p>
      ) : null}
      <RoomInboxPanel classNames={inbox} aria-label={labels.inboxListAriaLabel}>
        {roomsLoading ? (
          <EmptyGuidance
            classNames={empty}
            variant="panel"
            title={labels.loadingRoomsTitle}
            message={labels.loadingRoomsMessage}
          />
        ) : null}
        {!roomsLoading && rooms.length === 0 ? (
          <EmptyGuidance
            classNames={empty}
            variant="panel"
            title={searchEmpty ? labels.inboxSearchEmptyTitle : inboxEmptyTitle || labels.inboxEmptyTitle}
            message={searchEmpty ? labels.inboxSearchEmptyMessage : inboxEmptyMessage || labels.inboxEmptyMessage}
          >
            {searchEmpty ? null : inboxEmptyAction}
          </EmptyGuidance>
        ) : null}
        {!roomsLoading && rooms.length > 0 ? (
          <RoomInboxList
            classNames={inbox}
            items={rooms}
            listAriaLabel={labels.inboxListAriaLabel}
            emptyLabel={labels.inboxEmptyTitle}
            onSelect={onSelectRoom}
            leading={(row) => <InitialsAvatar classNames={avatar} name={row.title} size="sm" />}
            subtitle={inboxSubtitle}
          />
        ) : null}
      </RoomInboxPanel>
    </section>
  );

  const threadPane = !room ? null : (
    <RoomConversationShell
      classNames={shell}
      dropClassNames={drop}
      rootClassName={`${root}__thread`}
      as="section"
      dropOverlayLabel={labels.dropOverlay}
      accept={accept}
      onFiles={(files) => {
        setPane("chat");
        onFiles(files);
      }}
      header={
        <RoomHeader
          classNames={header}
          title={room.title}
          chips={room.chips}
          titleActionLabel={room.titleActionLabel}
          onTitleClick={room.onTitleClick}
          participants={room.participants ? [...room.participants] : undefined}
          participantsAriaLabel={room.participantsAriaLabel}
          navAriaLabel={labels.roomViewNavAriaLabel}
          nav={
            <SegmentToggle
              classNames={segments}
              ariaLabel={labels.roomViewNavAriaLabel}
              size="sm"
              value={pane}
              onChange={setPane}
              options={[
                {
                  value: "chat",
                  label: <MessageSquare size={16} aria-hidden="true" />,
                  ariaLabel: labels.roomViewChat,
                },
                {
                  value: "shared",
                  label: <Files size={16} aria-hidden="true" />,
                  ariaLabel: labels.roomViewShared,
                },
              ]}
            />
          }
          leadingAction={
            narrow && onBack ? (
              <ActionButton type="button" variant="ghost" aria-label={labels.backAriaLabel} title={labels.backAriaLabel} onClick={onBack}>
                <ArrowLeft size={16} aria-hidden="true" />
              </ActionButton>
            ) : undefined
          }
          actions={
            <>
              {headerMenu}
              {onCopyLink ? (
                <ActionButton type="button" variant="ghost" aria-label={labels.copyLinkAriaLabel} title={labels.copyLinkAriaLabel} onClick={onCopyLink}>
                  <Copy size={16} aria-hidden="true" />
                </ActionButton>
              ) : null}
              <ActionButton
                type="button"
                variant="ghost"
                aria-label={labels.findAriaLabel}
                title={labels.findAriaLabel}
                aria-expanded={side === "find"}
                onClick={() => setSide((current) => (current === "find" ? null : "find"))}
              >
                <Search size={16} aria-hidden="true" />
              </ActionButton>
              <ActionButton
                type="button"
                variant="ghost"
                aria-label={side === "context" ? labels.contextCloseAriaLabel : labels.contextAriaLabel}
                title={side === "context" ? labels.contextCloseAriaLabel : labels.contextAriaLabel}
                aria-expanded={side === "context"}
                onClick={() => setSide((current) => (current === "context" ? null : "context"))}
              >
                <PanelRight size={16} aria-hidden="true" />
              </ActionButton>
            </>
          }
        />
      }
      sidePanel={
        <RoomSidePanel
          classNames={sidePanel}
          open={side != null}
          showTitle={side !== "find"}
          title={side === "find" ? labels.find.title : labels.contextTitle}
        >
          {side === "find" ? (
            <RoomMessageFindPanel
              classNames={find}
              labels={labels.find}
              query={findQuery}
              onQueryChange={setFindQuery}
              onClear={() => setFindQuery("")}
              onClose={() => setSide(null)}
              results={findResults}
              onSelectResult={focusMessage}
            />
          ) : (
            <RoomContextPanel
              classNames={context}
              embedded
              flush
              labels={labels.context}
              entityPrimary={entityPrimary}
              entityFields={entityFields}
              entityHref={entityHref}
              onOpenEntity={onOpenEntity}
              participants={room.participants ? [...room.participants] : []}
              participantsAriaLabel={room.participantsAriaLabel}
              pins={messages
                .filter((item) => item.pinned && !item.deleted)
                .map<RoomContextPanelPin>((item) => ({
                  id: item.id,
                  messageId: item.id,
                  title: markdownToPlainPreview(item.bodyText, 80),
                  dateLabel: item.createdAtLabel,
                }))}
              onPinSelect={focusMessage}
            />
          )}
        </RoomSidePanel>
      }
      main={
        messagesLoading ? (
          <EmptyGuidance
            classNames={empty}
            variant="panel"
            title={labels.loadingThreadTitle}
            message={labels.loadingThreadMessage}
          />
        ) : pane === "shared" ? (
          <div role="tabpanel" aria-label={labels.roomViewShared}>
            <RoomSharedItemList
              classNames={shared}
              items={visibleShared}
              listAriaLabel={labels.sharedListAriaLabel}
              onOpen={(id) => {
                const item = sharedItems.find((row) => row.id === id);
                if (item) onOpenShared(item);
              }}
              toolbar={
                <UnderlineNav
                  classNames={nav}
                  mode="tabs"
                  aria-label={labels.roomViewShared}
                  activeId={sharedKind}
                  items={[
                    { id: "recent", label: labels.sharedRecent, onSelect: () => setSharedKind("recent") },
                    { id: "file", label: labels.sharedFiles, onSelect: () => setSharedKind("file") },
                    { id: "link", label: labels.sharedLinks, onSelect: () => setSharedKind("link") },
                  ]}
                />
              }
              toolbarActions={
                <TextField
                  classNames={field}
                  label={labels.sharedFilterPlaceholder}
                  hideLabel
                  value={sharedFilter}
                  onChange={setSharedFilter}
                  placeholder={labels.sharedFilterPlaceholder}
                  fullWidth
                />
              }
            >
              <EmptyGuidance
                classNames={empty}
                variant="panel"
                title={labels.sharedEmptyTitle}
                message={labels.sharedEmptyMessage}
              />
            </RoomSharedItemList>
          </div>
        ) : (
          <RoomConversationChatColumn
            classNames={shell}
            dock={
              <div aria-busy={submitting || undefined}>
                {composerError ? (
                  <p className={`${root}__alert`} role="alert">
                    {composerError}
                  </p>
                ) : null}
                <MentionComposer
                  key={room.id}
                  classNames={composer}
                  labels={labels.composer}
                  value={draft}
                  onChange={onDraftChange}
                  onSubmit={onSubmit}
                  submitting={submitting}
                  disabled={submitting}
                  showAttach={true}
                  fileAccept={accept}
                  pendingAttachments={pendingAttachments}
                  onFilesSelected={onFiles}
                  onRemovePendingAttachment={onRemovePendingAttachment}
                  mentionHits={mentionHits}
                  onMentionQueryChange={onMentionQueryChange}
                  onMentionInserted={onMentionInserted}
                  replyTo={replyTo}
                  onCancelReply={onCancelReply}
                />
              </div>
            }
          >
            {threadStatus}
            {messagesError ? (
              <p className={`${root}__alert`} role="alert">
                {messagesError}
              </p>
            ) : null}
            {actionError ? (
              <p className={`${root}__alert`} role="alert">
                {actionError}
              </p>
            ) : null}
            {hasMore ? <p className={`${root}__note`}>{labels.hasMore}</p> : null}
            <MessageThread
              classNames={thread}
              messages={messages.map((item) => ({
                ...item,
                belowBody: item.deleted ? null : (
                  <div className={`${root}__extra`}>
                    {(item.files ?? []).map((file) => (
                      <span key={file.id} className={`${root}__file`}>
                        <button type="button" onClick={() => onOpenAttachment?.(file.id)}>
                          {file.fileName}
                        </button>
                        {file.removable && onRemoveAttachment ? (
                          <button type="button" onClick={() => onRemoveAttachment(file.id)}>
                            {labels.removeFile}
                          </button>
                        ) : null}
                      </span>
                    ))}
                    {onToggleReaction ? (
                      <ReactionBar
                        classNames={reactions}
                        items={item.reactions ?? []}
                        listAriaLabel={labels.reactionsList}
                        addAriaLabel={labels.react}
                        onToggle={(code) => onToggleReaction(item.id, code)}
                        onAdd={(code) => onToggleReaction(item.id, code)}
                        emojiAdd={{ listAriaLabel: labels.chooseReaction }}
                      />
                    ) : null}
                  </div>
                ),
              }))}
              listAriaLabel={labels.messagesAriaLabel}
              emptyLabel={labels.emptyThreadTitle}
              editingId={editingId}
              renderEditSlot={renderEditSlot}
              resolveActions={(row) => {
                const source = messages.find((item) => item.id === row.id);
                if (!source || source.deleted) return [];
                const actions = [];
                if (onReply) {
                  actions.push({
                    id: "reply",
                    label: labels.reply,
                    icon: <Reply size={16} aria-hidden="true" />,
                    onClick: () => onReply(source.id),
                  });
                }
                if (onTogglePin) {
                  actions.push({
                    id: "pin",
                    label: source.pinned ? labels.unpin : labels.pin,
                    icon: <Pin size={16} aria-hidden="true" />,
                    onClick: () => onTogglePin(source),
                  });
                }
                if (onEdit && source.mine) {
                  actions.push({
                    id: "edit",
                    label: labels.edit,
                    icon: <Pencil size={16} aria-hidden="true" />,
                    onClick: () => onEdit(source),
                  });
                }
                if (onDelete && source.mine) {
                  actions.push({
                    id: "delete",
                    label: labels.delete,
                    danger: true,
                    icon: <Trash2 size={16} aria-hidden="true" />,
                    onClick: () => onDelete(source.id),
                  });
                }
                return actions;
              }}
              emptyContent={
                <EmptyGuidance
                  classNames={empty}
                  variant="canvas"
                  title={labels.emptyThreadTitle}
                  message={labels.emptyThreadMessage}
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
    <div className={root}>
      <div className={`${root}__grid`}>
        {narrow ? (
          room ? threadPane : inboxPane
        ) : room ? (
          <ResizableColumns
            classNames={columns}
            left={inboxPane}
            right={threadPane}
            labels={{
              separatorAriaLabel: labels.resizeSeparator,
              collapseAriaLabel: labels.collapseInbox,
              expandAriaLabel: labels.expandInbox,
            }}
          />
        ) : (
          inboxPane
        )}
      </div>
    </div>
  );
}
