import { useRef, useState } from "react";

import { PUC_PREFIX } from "../../app/bemPrefix";
import {
  EntityUnfurlCard,
  entityUnfurlCardBemClasses,
  MentionComposer,
  mentionComposerBemClasses,
  MentionMenu,
  mentionMenuBemClasses,
  MentionText,
  mentionTextBemClasses,
  MessageThread,
  messageThreadBemClasses,
  ReactionBar,
  reactionBarBemClasses,
  RoomHeader,
  roomHeaderBemClasses,
  RoomInboxList,
  roomInboxListBemClasses,
} from "../../components/collaboration";
import { IconButton } from "../../components/actions";
import {
  ConversationError,
  ConversationHeader,
  ConversationUserMessage,
  ConversationStatus,
  ConversationWorkspace,
  GovernedConfirmation,
  MessageActionBar,
} from "../../components/conversation";
import { UnifiedAvatar } from "../../components/layout/UnifiedAvatar";
import type { CatalogEntryDraft } from "../types";

const mentionTextCn = mentionTextBemClasses(PUC_PREFIX);
const mentionMenuCn = mentionMenuBemClasses(PUC_PREFIX);
const composerCn = mentionComposerBemClasses(PUC_PREFIX);
const threadCn = messageThreadBemClasses(PUC_PREFIX);
const unfurlCn = entityUnfurlCardBemClasses(PUC_PREFIX);
const reactionCn = reactionBarBemClasses(PUC_PREFIX);
const inboxCn = roomInboxListBemClasses(PUC_PREFIX);
const headerCn = roomHeaderBemClasses(PUC_PREFIX);

function MentionMenuDemo() {
  const anchorRef = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(true);
  return (
    <div>
      <button ref={anchorRef} type="button" onClick={() => setOpen(true)}>
        Anchor
      </button>
      <MentionMenu
        open={open}
        anchorRef={anchorRef}
        classNames={mentionMenuCn}
        listAriaLabel="Mentions"
        emptyLabel="No matches"
        onDismiss={() => setOpen(false)}
        onSelect={() => setOpen(false)}
        hits={[
          {
            id: "u1",
            kind: "user",
            label: "Ana Silva",
            groupLabel: "People",
            subtitle: "ana@delpi",
          },
          {
            id: "o1",
            kind: "order",
            label: "102942",
            groupLabel: "Objects",
          },
        ]}
      />
    </div>
  );
}

function MentionComposerDemo() {
  const [value, setValue] = useState("Hello @");
  return (
    <MentionComposer
      classNames={composerCn}
      value={value}
      onChange={setValue}
      onSubmit={() => undefined}
      showAttach
      mentionHits={[
        { id: "u1", kind: "user", label: "Ana", groupLabel: "People" },
      ]}
      labels={{
        placeholder: "Write a message",
        sendAriaLabel: "Send",
        attachAriaLabel: "Attach",
        mentionListAriaLabel: "Mentions",
        mentionEmptyLabel: "No matches",
      }}
    />
  );
}

export const collaborationCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "collaboration.MentionText",
    family: "collaboration",
    exportName: "MentionText",
    title: "MentionText",
    description: "Render de corpo com chips de menção.",
    docAnchor: "mentiontext",
    demos: [
      {
        id: "basic",
        label: "Basic",
        render: () => (
          <MentionText
            classNames={mentionTextCn}
            text="Falar com @Ana sobre o pedido"
            mentions={[{ kind: "user", label: "@Ana", href: "/apps/demo/ana", title: "Ana" }]}
          />
        ),
      },
    ],
  },
  {
    id: "collaboration.MentionMenu",
    family: "collaboration",
    exportName: "MentionMenu",
    title: "MentionMenu",
    description: "Listbox @ via AnchoredPanelPortal.",
    docAnchor: "mentionmenu",
    demos: [{ id: "basic", label: "Basic", render: () => <MentionMenuDemo /> }],
  },
  {
    id: "collaboration.MentionComposer",
    family: "collaboration",
    exportName: "MentionComposer",
    title: "MentionComposer",
    description: "Composer com textarea no kit.",
    docAnchor: "mentioncomposer",
    demos: [{ id: "basic", label: "Basic", render: () => <MentionComposerDemo /> }],
  },
  {
    id: "collaboration.MessageThread",
    family: "collaboration",
    exportName: "MessageThread",
    title: "MessageThread",
    description: "Thread de mensagens.",
    docAnchor: "messagethread",
    demos: [
      {
        id: "basic",
        label: "Basic",
        render: () => (
          <MessageThread
            classNames={threadCn}
            listAriaLabel="Messages"
            emptyLabel="Empty"
            messages={[
              {
                id: "1",
                kind: "text",
                bodyText: "Oi @Ana",
                authorName: "Bruno",
                createdAtLabel: "10:00",
                mentions: [{ kind: "user", label: "@Ana" }],
              },
              {
                id: "2",
                kind: "system",
                bodyText: "Sala criada",
                createdAtLabel: "10:01",
              },
            ]}
          />
        ),
      },
    ],
  },
  {
    id: "collaboration.EntityUnfurlCard",
    family: "collaboration",
    exportName: "EntityUnfurlCard",
    title: "EntityUnfurlCard",
    description: "Unfurl genérico.",
    docAnchor: "entityunfurlcard",
    demos: [
      {
        id: "ok",
        label: "Accessible",
        render: () => (
          <EntityUnfurlCard
            classNames={unfurlCn}
            title="Pedido 102942"
            kindLabel="Order"
            fields={[{ id: "c", label: "Customer", value: "ACME" }]}
            openLabel="Open"
            onOpen={() => undefined}
          />
        ),
      },
      {
        id: "denied",
        label: "Denied",
        render: () => (
          <EntityUnfurlCard
            classNames={unfurlCn}
            title="Pedido 102942"
            accessible={false}
            deniedLabel="No access"
          />
        ),
      },
    ],
  },
  {
    id: "collaboration.ReactionBar",
    family: "collaboration",
    exportName: "ReactionBar",
    title: "ReactionBar",
    description: "Reações.",
    docAnchor: "reactionbar",
    demos: [
      {
        id: "basic",
        label: "Basic",
        render: () => (
          <ReactionBar
            classNames={reactionCn}
            listAriaLabel="Reactions"
            addAriaLabel="Add"
            items={[{ code: "thumbsup", label: "👍", count: 2, reactedByMe: true }]}
            availableCodes={[
              { code: "thumbsup", label: "👍" },
              { code: "heart", label: "❤️" },
            ]}
            onToggle={() => undefined}
            onAdd={() => undefined}
          />
        ),
      },
    ],
  },
  {
    id: "collaboration.RoomInboxList",
    family: "collaboration",
    exportName: "RoomInboxList",
    title: "RoomInboxList",
    description: "Inbox de salas.",
    docAnchor: "roominboxlist",
    demos: [
      {
        id: "basic",
        label: "Basic",
        render: () => (
          <RoomInboxList
            classNames={inboxCn}
            listAriaLabel="Inbox"
            emptyLabel="Empty"
            items={[
              {
                id: "r1",
                title: "Pedido 102942",
                preview: "Atualização do pedido",
                unreadCount: 2,
                kindLabel: "Entity",
              },
            ]}
          />
        ),
      },
    ],
  },
  {
    id: "collaboration.RoomHeader",
    family: "collaboration",
    exportName: "RoomHeader",
    title: "RoomHeader",
    description: "Cabeçalho da sala.",
    docAnchor: "roomheader",
    demos: [
      {
        id: "basic",
        label: "Basic",
        render: () => (
          <RoomHeader
            classNames={headerCn}
            title="Pedido 102942"
            subtitle="Entity room"
            participantsAriaLabel="Members"
            participants={[
              { id: "1", name: "Ana Silva" },
              { id: "2", name: "Bruno Costa" },
            ]}
          />
        ),
      },
    ],
  },
  {
    id: "collaboration.ConversationWorkspace",
    family: "collaboration",
    exportName: "ConversationWorkspace",
    title: "ConversationWorkspace",
    description:
      "Shell chat-first: header leve + corpo rolável com coluna centrada + rodapé ancorado.",
    propsSummary: [
      "header",
      "banner",
      "children",
      "footer",
      "density",
      "bodyRef",
      "onBodyScroll",
      "aria-label",
    ],
    demos: [
      {
        id: "empty",
        label: "Recepção (vazio)",
        render: () => (
          <div style={{ height: 320, border: "1px dashed var(--delpi-ui-border, #e6e6e6)" }}>
            <ConversationWorkspace
              aria-label="Conversa"
              header={<ConversationHeader title="DÉLIA" subtitle="Inteligência operacional DELPI" />}
              footer={<div style={{ padding: "8px 0", borderTop: "1px solid var(--delpi-ui-border, #e6e6e6)", textAlign: "center", fontSize: 12 }}>composer (slot)</div>}
            >
              <div style={{ margin: "auto", textAlign: "center" }}>
                Recepção / estado vazio
              </div>
            </ConversationWorkspace>
          </div>
        ),
      },
      {
        id: "active-long",
        label: "Conversa ativa + longa",
        render: () => (
          <div style={{ height: 320, border: "1px dashed var(--delpi-ui-border, #e6e6e6)" }}>
            <ConversationWorkspace
              aria-label="Conversa"
              header={<ConversationHeader title="DÉLIA" compact />}
              footer={<div style={{ padding: "8px 0", borderTop: "1px solid var(--delpi-ui-border, #e6e6e6)", textAlign: "center", fontSize: 12 }}>composer (slot)</div>}
            >
              {Array.from({ length: 12 }, (_, i) => (
                <p key={i} style={{ margin: 0, padding: "6px 10px", borderRadius: 8, background: "var(--delpi-ui-surface-muted, #f1f5f9)", fontSize: 13 }}>
                  Turno {i + 1} da conversa
                </p>
              ))}
            </ConversationWorkspace>
          </div>
        ),
      },
    ],
  },
  {
    id: "collaboration.ConversationHeader",
    family: "collaboration",
    exportName: "ConversationHeader",
    title: "ConversationHeader",
    description:
      "Chrome conversacional leve: título + subtítulo + leading + actions.",
    propsSummary: ["title", "subtitle", "leading", "actions", "compact", "titleAs"],
    demos: [
      {
        id: "full",
        label: "Completo",
        render: () => (
          <ConversationHeader
            title="DÉLIA"
            subtitle="Inteligência operacional DELPI"
            actions={<button type="button">Ação</button>}
          />
        ),
      },
      {
        id: "compact",
        label: "Compacto (dock)",
        render: () => (
          <div style={{ maxWidth: 320 }}>
            <ConversationHeader title="DÉLIA" subtitle="Inteligência operacional DELPI" compact />
          </div>
        ),
      },
    ],
  },
  {
    id: "collaboration.ConversationUserMessage",
    family: "collaboration",
    exportName: "ConversationUserMessage",
    title: "ConversationUserMessage",
    description: "Mensagem de usuário à direita, com autor, avatar e texto literal recebidos por slot.",
    propsSummary: ["children", "avatar", "authorLabel", "density", "className", "contentClassName"],
    demos: [
      {
        id: "basic",
        label: "Básico",
        render: () => (
          <ConversationUserMessage
            authorLabel="Você"
            avatar={<UnifiedAvatar kind="person" label="Você" size="sm" fallbackText="Ana Lima" />}
          >
            Como está a situação deste pedido?
          </ConversationUserMessage>
        ),
      },
      {
        id: "long",
        label: "Mensagem longa e multiline",
        render: () => (
          <ConversationUserMessage
            authorLabel="Você"
            avatar={<UnifiedAvatar kind="person" label="Você" size="sm" />}
          >
            {"Primeira linha da pergunta.\nOutra linha com uma descrição extensa para validar quebra de linha, alinhamento e conteúdo técnico como <item> renderizado literalmente."}
          </ConversationUserMessage>
        ),
      },
      {
        id: "compact",
        label: "Compacto (dock)",
        render: () => (
          <div style={{ maxWidth: 320 }}>
            <ConversationUserMessage
              authorLabel="Você"
              density="compact"
              avatar={<UnifiedAvatar kind="person" label="Você" size="sm" />}
            >
              Uma pergunta em espaço reduzido.
            </ConversationUserMessage>
          </div>
        ),
      },
      {
        id: "no-avatar",
        label: "Sem avatar",
        render: () => (
          <ConversationUserMessage authorLabel="Usuário">Sem avatar disponível.</ConversationUserMessage>
        ),
      },
      {
        id: "long-author",
        label: "Autor extenso",
        render: () => (
          <div style={{ maxWidth: 320 }}>
            <ConversationUserMessage authorLabel="Participante com identificação muito extensa">
              Texto breve.
            </ConversationUserMessage>
          </div>
        ),
      },
    ],
  },
  {
    id: "collaboration.ConversationStatus",
    family: "collaboration",
    exportName: "ConversationStatus",
    title: "ConversationStatus",
    description:
      "Estado semântico inline de mensagem: ícone decorativo + StatusBadge. Apresentação pura — o consumidor resolve label/tone.",
    propsSummary: [
      "label",
      "tone",
      "icon",
      "description",
      "density",
      "aria-label",
      "className",
    ],
    demos: [
      {
        id: "tones",
        label: "Tons (info/warning/danger/neutral)",
        render: () => (
          <div style={{ display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-start" }}>
            <ConversationStatus tone="info" label="Esclarecimento necessário"
              icon={<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>} />
            <ConversationStatus tone="warning" label="Confirmação pendente"
              icon={<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>} />
            <ConversationStatus tone="danger" label="Acesso não autorizado"
              icon={<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>} />
            <ConversationStatus tone="neutral" label="Estado neutro" />
          </div>
        ),
      },
      {
        id: "compact-long",
        label: "Compacto + label longa",
        render: () => (
          <div style={{ maxWidth: 320 }}>
            <ConversationStatus
              tone="warning"
              density="compact"
              label="Pré-condição pendente — a fonte pediu uma informação adicional antes de continuar"
            />
          </div>
        ),
      },
      {
        id: "no-icon",
        label: "Sem ícone",
        render: () => <ConversationStatus tone="info" label="Estado informativo" />,
      },
    ],
  },
  {
    id: "collaboration.GovernedConfirmation",
    family: "collaboration",
    exportName: "GovernedConfirmation",
    title: "GovernedConfirmation",
    description:
      "Superfície inline de decisão governada: título + descrição/preview opcionais + Confirmar/Cancelar (ActionButton). Apresentação pura.",
    propsSummary: [
      "title",
      "description",
      "preview",
      "confirmLabel",
      "cancelLabel",
      "onConfirm",
      "onCancel",
      "loading",
      "density",
      "tone",
      "aria-label",
    ],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <div style={{ maxWidth: 480 }}>
            <GovernedConfirmation
              description="Revise a operação antes de continuar."
              onConfirm={() => {}}
              onCancel={() => {}}
            />
          </div>
        ),
      },
      {
        id: "loading",
        label: "Loading (double-submit guard)",
        render: () => (
          <div style={{ maxWidth: 480 }}>
            <GovernedConfirmation
              loading
              onConfirm={() => {}}
              onCancel={() => {}}
            />
          </div>
        ),
      },
      {
        id: "compact",
        label: "Compacto (dock)",
        render: () => (
          <div style={{ maxWidth: 320 }}>
            <GovernedConfirmation
              density="compact"
              onConfirm={() => {}}
              onCancel={() => {}}
            />
          </div>
        ),
      },
    ],
  },
  {
    id: "collaboration.ConversationError",
    family: "collaboration",
    exportName: "ConversationError",
    title: "ConversationError",
    description:
      "Falha de interação no footer: role=alert, ícone + título + descrição opcional + ação opcional (ActionButton). Apresentação pura — sem retry automático.",
    propsSummary: [
      "title",
      "description",
      "icon",
      "actionLabel",
      "onAction",
      "actionDisabled",
      "loading",
      "density",
      "className",
    ],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <div style={{ maxWidth: 480 }}>
            <ConversationError
              title="Não foi possível concluir esta solicitação."
              description="Sua mensagem foi preservada."
            />
          </div>
        ),
      },
      {
        id: "action",
        label: "Com ação de recuperação",
        render: () => (
          <div style={{ maxWidth: 480 }}>
            <ConversationError
              title="Não foi possível concluir esta solicitação."
              description="Sua mensagem foi preservada."
              actionLabel="Tentar novamente"
              onAction={() => {}}
            />
          </div>
        ),
      },
      {
        id: "compact",
        label: "Compacto (dock)",
        render: () => (
          <div style={{ maxWidth: 320 }}>
            <ConversationError
              title="Não foi possível concluir."
              density="compact"
            />
          </div>
        ),
      },
    ],
  },
  {
    id: "collaboration.MessageActionBar",
    family: "collaboration",
    exportName: "MessageActionBar",
    title: "MessageActionBar",
    description:
      "Barra de ações secundárias de uma mensagem — compõe IconButton; chrome subordinado, sem lógica de negócio.",
    propsSummary: [
      "children",
      "visibility",
      "density",
      "align",
      "aria-label",
      "className",
    ],
    demos: [
      {
        id: "always",
        label: "Sempre visível",
        render: () => (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 600 }}>DÉLIA</span>
            <MessageActionBar visibility="always" aria-label="Ações da resposta">
              <IconButton aria-label="Copiar resposta">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </IconButton>
            </MessageActionBar>
          </div>
        ),
      },
      {
        id: "hover-focus",
        label: "Reveal em hover/focus (padrão)",
        render: () => (
          <div
            className="delpi-ui-message-action-scope"
            style={{ display: "flex", alignItems: "center", gap: 6, padding: 8, border: "1px dashed var(--delpi-ui-border, #e6e6e6)", borderRadius: 8 }}
          >
            <span style={{ fontSize: 12, fontWeight: 600 }}>DÉLIA</span>
            <MessageActionBar aria-label="Ações da resposta">
              <IconButton aria-label="Copiar resposta">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </IconButton>
            </MessageActionBar>
          </div>
        ),
      },
    ],
  },
];
