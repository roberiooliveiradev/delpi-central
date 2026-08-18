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
];
