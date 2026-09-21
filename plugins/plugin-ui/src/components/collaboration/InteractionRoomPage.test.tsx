import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InteractionRoomPage, INTERACTION_ROOM_PAGE_LABELS_PT } from "./InteractionRoomPage";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");

afterEach(() => {
  cleanup();
});

const labels = INTERACTION_ROOM_PAGE_LABELS_PT;

function renderRoom() {
  return render(
    <InteractionRoomPage
      labels={labels}
      inboxQuery=""
      onInboxQueryChange={() => undefined}
      chips={[{ id: "all", label: "Todas", active: true, onSelect: () => undefined }]}
      rooms={[{ id: "room-1", title: "Processo piloto", selected: true }]}
      onRefresh={() => undefined}
      onSelectRoom={() => undefined}
      room={{ id: "room-1", title: "Processo piloto" }}
      messages={[
        {
          id: "m1",
          kind: "text",
          bodyText: "olá https://delpi.example/doc",
          createdAtLabel: "hoje",
          authorName: "Ana",
          mine: true,
          pinned: true,
          reactions: [],
          files: [{ id: "f1", fileName: "foto.png", removable: true }],
        },
      ]}
      draft=""
      onDraftChange={() => undefined}
      onSubmit={() => undefined}
      onFiles={() => undefined}
      accept="image/png"
      onReply={() => undefined}
      onTogglePin={() => undefined}
      onEdit={() => undefined}
      onDelete={() => undefined}
      onToggleReaction={() => undefined}
      sharedItems={[
        {
          id: "f1",
          kind: "file",
          title: "foto.png",
          ariaLabel: "Abrir foto.png",
        },
        {
          id: "l1",
          kind: "link",
          title: "https://delpi.example/doc",
          href: "https://delpi.example/doc",
          ariaLabel: "Abrir link",
        },
      ]}
      onOpenShared={() => undefined}
      entityPrimary="PROC-0001"
      entityFields={[{ label: "Processo", value: "Processo piloto" }]}
      entityHref="/processo"
      onOpenEntity={() => undefined}
    />,
  );
}

describe("InteractionRoomPage", () => {
  it("é a página canônica e não busca dados", () => {
    expect(source).toMatch(/MentionComposer/);
    expect(source).toMatch(/showAttach=\{true\}/);
    expect(source).toMatch(/fileAccept=\{accept\}/);
    expect(source).toMatch(/ReactionBar/);
    expect(source).toMatch(/ReactionQuickBar/);
    expect(source).toMatch(/reactionLabelForCode/);
    expect(source).toMatch(/resolveActionExtras/);
    expect(source).not.toMatch(/emojiAdd=\{\{/);
    expect(source).toMatch(/RoomContextPanel/);
    expect(source).toMatch(/RoomSidePanel/);
    expect(source).toMatch(/RoomMessageFindPanel/);
    expect(source).toMatch(/RoomSharedItemList/);
    expect(source).toMatch(/sharedRecent/);
    expect(source).toMatch(/sharedLinks/);
    expect(source).not.toMatch(/\bfetch\(/);
    expect(source).not.toMatch(/commercial/);
  });

  it("mostra glyph da reação na bolha, sem o seletor + embutido", () => {
    render(
      <InteractionRoomPage
        labels={labels}
        inboxQuery=""
        onInboxQueryChange={() => undefined}
        chips={[]}
        rooms={[{ id: "room-1", title: "Sala", selected: true }]}
        onRefresh={() => undefined}
        onSelectRoom={() => undefined}
        room={{ id: "room-1", title: "Sala" }}
        messages={[
          {
            id: "m1",
            kind: "text",
            bodyText: "olá",
            createdAtLabel: "hoje",
            authorName: "Ana",
            mine: true,
            reactions: [{ code: "check", label: "check", count: 1, reactedByMe: true }],
          },
        ]}
        draft=""
        onDraftChange={() => undefined}
        onSubmit={() => undefined}
        onFiles={() => undefined}
        accept="*/*"
        sharedItems={[]}
        onOpenShared={() => undefined}
        onToggleReaction={() => undefined}
      />,
    );
    expect(screen.getByRole("button", { name: "✅" })).toBeTruthy();
    expect(screen.queryByText("check")).toBeNull();
    expect(screen.queryByLabelText(labels.react)).toBeNull();
  });

  it("mostra conversa, anexo, painel e itens compartilhados", () => {
    renderRoom();
    expect(screen.getByLabelText(labels.inboxTitle)).toBeTruthy();
    expect(screen.getByLabelText(labels.composer.attachAriaLabel)).toBeTruthy();
    expect(screen.getByRole("button", { name: labels.contextAriaLabel })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: labels.roomViewShared }));
    expect(screen.getByRole("tab", { name: labels.sharedRecent })).toBeTruthy();
    expect(screen.getByRole("tab", { name: labels.sharedLinks })).toBeTruthy();
    expect(screen.getByText("foto.png")).toBeTruthy();
  });

  it("abre o painel da sala com a mensagem fixada", () => {
    renderRoom();
    fireEvent.click(screen.getByRole("button", { name: labels.contextAriaLabel }));
    expect(screen.getByRole("heading", { name: /Fixadas/ })).toBeTruthy();
    expect(screen.getByText("PROC-0001")).toBeTruthy();
  });

  it("copia o link quando o host entrega o comando", () => {
    const onCopy = vi.fn();
    render(
      <InteractionRoomPage
        inboxQuery=""
        onInboxQueryChange={() => undefined}
        chips={[]}
        rooms={[]}
        onRefresh={() => undefined}
        onSelectRoom={() => undefined}
        room={{ id: "room-1", title: "Sala" }}
        messages={[]}
        draft=""
        onDraftChange={() => undefined}
        onSubmit={() => undefined}
        onFiles={() => undefined}
        accept="*/*"
        sharedItems={[]}
        onOpenShared={() => undefined}
        onCopyLink={onCopy}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: labels.copyLinkAriaLabel }));
    expect(onCopy).toHaveBeenCalledOnce();
  });
});
