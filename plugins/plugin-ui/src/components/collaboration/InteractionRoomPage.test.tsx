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

const baseProps = {
  labels,
  inboxQuery: "",
  onInboxQueryChange: () => undefined,
  chips: [{ id: "all", label: "Todas", active: true, onSelect: () => undefined }],
  rooms: [{ id: "room-1", title: "Processo piloto", selected: true }],
  onRefresh: () => undefined,
  onSelectRoom: () => undefined,
  room: { id: "room-1", title: "Processo piloto" },
  draft: "",
  onDraftChange: () => undefined,
  onSubmit: () => undefined,
  onFiles: () => undefined,
  accept: "image/png",
  sharedItems: [] as const,
  onOpenShared: () => undefined,
};

function renderRoom() {
  return render(
    <InteractionRoomPage
      {...baseProps}
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
    expect(source).toMatch(/resolveExtraActions/);
    expect(source).toMatch(/renderComposer/);
    expect(source).toMatch(/layout === "thread"/);
    expect(source).toMatch(/data-layout=\{layout\}/);
    expect(source).toMatch(/\bfill\b/);
    expect(source).toMatch(/shouldStickThreadToBottom/);
    const roomCss = readFileSync(
      join(dir, "../../styles/interaction-room-page.css"),
      "utf8",
    );
    expect(roomCss).not.toMatch(/min-height:\s*calc\(\s*100vh/);
    expect(roomCss).not.toMatch(/height:\s*calc\(\s*100vh/);
    expect(roomCss).toMatch(/min-height:\s*0/);
    expect(roomCss).toMatch(/height:\s*100%/);
    expect(source).toMatch(/onLoadOlder/);
    expect(source).toMatch(/resolveAttachmentImageSrc/);
    expect(source).toMatch(/onInlineImagesInserted/);
    expect(source).toMatch(/AttachmentPreviewStrip/);
    expect(source).toMatch(/mode=\{canManageAttachments \? "manage" : "preview"\}/);
    expect(source).toMatch(/onParentQuoteClick=\{focusMessage\}/);
    expect(source).toMatch(/portalScopeClassName/);
    expect(source).toMatch(/actionsToolbarAriaLabel/);
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

  it("completa labels PT do composer sem depender de fallback EN", () => {
    expect(labels.composer.formatBoldAriaLabel).toBe("Negrito");
    expect(labels.composer.formatItalicAriaLabel).toBe("Itálico");
    expect(labels.composer.formatLinkAriaLabel).toBe("Link");
    expect(labels.composer.formatEmojiAriaLabel).toBe("Emoji");
    expect(labels.composer.pendingDocumentsHeading).toBe("Arquivos a enviar");
    expect(labels.actionsToolbarAriaLabel).toBe("Opções da mensagem");
    expect(labels.find.title).toMatch(/Localizar/i);
    expect(labels.loadOlder).toMatch(/anteriores/i);
  });

  it("mostra glyph da reação na bolha, sem o seletor + embutido", () => {
    render(
      <InteractionRoomPage
        {...baseProps}
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

  it("usa mode manage e remove só anexos removable", () => {
    const onRemoveAttachment = vi.fn();
    render(
      <InteractionRoomPage
        {...baseProps}
        messages={[
          {
            id: "m1",
            kind: "text",
            bodyText: "olá",
            createdAtLabel: "hoje",
            authorName: "Ana",
            mine: true,
            files: [
              { id: "f1", fileName: "foto.png", removable: true },
              { id: "f2", fileName: "doc.pdf", removable: false },
            ],
          },
        ]}
        onRemoveAttachment={onRemoveAttachment}
      />,
    );
    expect(screen.getByRole("button", { name: labels.attachmentRemoveAriaLabel("foto.png") })).toBeTruthy();
    expect(screen.queryByRole("button", { name: labels.attachmentRemoveAriaLabel("doc.pdf") })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: labels.attachmentRemoveAriaLabel("foto.png") }));
    expect(onRemoveAttachment).toHaveBeenCalledWith("f1");
  });

  it("mostra botão load older quando hasMore e onLoadOlder", () => {
    const onLoadOlder = vi.fn();
    render(
      <InteractionRoomPage
        {...baseProps}
        messages={[]}
        hasMore
        onLoadOlder={onLoadOlder}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: labels.loadOlder }));
    expect(onLoadOlder).toHaveBeenCalledOnce();
    expect(screen.queryByText(labels.hasMore)).toBeNull();
  });

  it("mantém nota hasMore quando não há onLoadOlder", () => {
    render(
      <InteractionRoomPage
        {...baseProps}
        messages={[]}
        hasMore
      />,
    );
    expect(screen.getByText(labels.hasMore)).toBeTruthy();
    expect(screen.queryByRole("button", { name: labels.loadOlder })).toBeNull();
  });

  it("layout thread oculta inbox e resize", () => {
    render(
      <InteractionRoomPage
        {...baseProps}
        layout="thread"
        messages={[]}
      />,
    );
    expect(screen.queryByLabelText(labels.inboxTitle)).toBeNull();
    expect(screen.queryByLabelText(labels.resizeSeparator)).toBeNull();
    expect(screen.getByLabelText(labels.composer.attachAriaLabel)).toBeTruthy();
  });

  it("resolveExtraActions concatena após ações canônicas", () => {
    render(
      <InteractionRoomPage
        {...baseProps}
        messages={[
          {
            id: "m1",
            kind: "text",
            bodyText: "olá",
            createdAtLabel: "hoje",
            authorName: "Ana",
            mine: true,
          },
        ]}
        onReply={() => undefined}
        resolveExtraActions={() => [
          {
            id: "task",
            label: "Criar tarefa",
            onClick: () => undefined,
          },
        ]}
      />,
    );
    expect(source).toMatch(/\[\.\.\.actions, \.\.\.extras\]/);
  });

  it("renderComposer substitui o MentionComposer do dock", () => {
    render(
      <InteractionRoomPage
        {...baseProps}
        messages={[]}
        renderComposer={<div data-testid="custom-composer">Composer host</div>}
      />,
    );
    expect(screen.getByTestId("custom-composer")).toBeTruthy();
    expect(screen.queryByLabelText(labels.composer.attachAriaLabel)).toBeNull();
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
