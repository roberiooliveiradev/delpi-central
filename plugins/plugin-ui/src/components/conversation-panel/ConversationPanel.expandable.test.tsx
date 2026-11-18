/* EVA-PRC-CONVERSATION-EXPANDABLE-HOST-MODAL — a mesma conversa abre em
 * modal contido no host do MFE, sem remount do painel (rascunho,
 * anexos pendentes e edição preservados) e sem cobrir a sidebar. */

import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { ConversationPanel } from "./ConversationPanel";
import type {
  ConversationApi,
  ConversationComment,
} from "./ConversationPanel";

const SCOPE = "test-mfe-scope";
let host: HTMLDivElement;

beforeEach(() => {
  host = document.createElement("div");
  host.className = SCOPE;
  document.body.appendChild(host);
});

afterEach(() => {
  cleanup();
  host.remove();
});

function comment(partial: Partial<ConversationComment>): ConversationComment {
  return {
    id: "c-1",
    requestId: "req-1",
    authorId: "u-1",
    authorName: "Ana Silva",
    body: "mensagem",
    version: 1,
    isMine: false,
    createdAt: "2026-11-20T10:00:00Z",
    updatedAt: null,
    edited: false,
    ...partial,
  };
}

function apiOf(items: ConversationComment[]): ConversationApi {
  return {
    listComments: async () => items,
    createComment: async () => comment({ id: "created" }),
    createCommentWithAttachments: async () => ({
      comment: comment({ id: "created" }),
      attachments: [],
    }),
    updateComment: async () => comment({ id: "updated" }),
    listAttachments: async () => [],
    uploadAttachment: async () => ({
      id: "a-1",
      fileName: "f.png",
      mediaType: "image/png",
      sizeBytes: 1,
    }),
    downloadAttachment: async () => new Blob(["x"]),
    deleteAttachment: async () => undefined,
  };
}

function renderPanel(extra?: Record<string, unknown>) {
  return render(
    <ConversationPanel
      requestId="req-1"
      api={apiOf([comment({}), comment({ id: "c-2", body: "resposta" })])}
      canComment
      portalScopeClassName={SCOPE}
      expandable
      {...extra}
    />,
  );
}

function openExpanded(getByLabelText: (l: string) => HTMLElement) {
  fireEvent.click(getByLabelText("Expandir conversa"));
}

function expandedDialog(): HTMLElement | null {
  return host.querySelector<HTMLElement>("[role='dialog']");
}

describe("ConversationPanel — modo expandido (opt-in)", () => {
  it("sem `expandable`, não renderiza o botão Expandir", async () => {
    const { queryByLabelText } = render(
      <ConversationPanel
        requestId="req-1"
        api={apiOf([])}
        canComment
        portalScopeClassName={SCOPE}
      />,
    );
    await waitFor(() =>
      expect(queryByLabelText("Expandir conversa")).toBeNull(),
    );
  });

  it("abre modal host-contained (fill), recolhe e devolve foco ao gatilho", async () => {
    const { getByLabelText, queryByLabelText } = renderPanel();
    const trigger = getByLabelText("Expandir conversa");

    openExpanded(getByLabelText);

    await waitFor(() => expect(expandedDialog()).not.toBeNull());
    const dialog = expandedDialog()!;
    /* contido no host do MFE — não no document.body nem cobrindo a sidebar */
    expect(host.contains(dialog)).toBe(true);
    expect(
      host.querySelector("[data-modal-contained='true']"),
    ).not.toBeNull();
    /* o diálogo mostra a mesma conversa: título + composer */
    expect(dialog.textContent).toContain("Conversa sobre a solicitação");
    expect(dialog.querySelector("[contenteditable='true']")).not.toBeNull();
    /* uma única superfície ativa — o card vira placeholder atrás do overlay */
    expect(
      document.querySelectorAll(
        ".delpi-ui-conversation-panel .delpi-ui-conversation-panel__frame",
      ).length,
    ).toBe(1);

    fireEvent.click(dialog.querySelector(
      "button[aria-label='Recolher conversa']",
    )!);

    await waitFor(() => expect(expandedDialog()).toBeNull());
    /* superfície volta ao card */
    expect(
      document.querySelector(
        ".delpi-ui-conversation-panel:not(.delpi-ui-conversation-panel--expanded) .delpi-ui-conversation-panel__frame",
      ),
    ).not.toBeNull();
    /* foco retorna ao gatilho que abriu o modal */
    expect(document.activeElement).toBe(trigger);
  });

  it("fecha com Escape e o rascunho digitado sobrevive ao ciclo", async () => {
    const { getByLabelText, container } = renderPanel();

    const surface = () =>
      document.querySelector<HTMLElement>("[contenteditable='true']")!;
    fireEvent.input(surface(), {
      target: { textContent: "rascunho preservado" },
    });
    await waitFor(() =>
      expect(surface().textContent).toContain("rascunho"),
    );

    openExpanded(getByLabelText);
    await waitFor(() => expect(expandedDialog()).not.toBeNull());
    /* mesmo painel, mesmo draft — reidratado no composer do modal */
    await waitFor(() =>
      expect(surface().textContent).toContain("rascunho preservado"),
    );

    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => expect(expandedDialog()).toBeNull());
    await waitFor(() =>
      expect(
        container.querySelector("[contenteditable='true']")!.textContent,
      ).toContain("rascunho preservado"),
    );
  });

  it("mantém o anexo pendente ao expandir e recolher", async () => {
    const { getByLabelText, container } = renderPanel();

    const fileInput = () =>
      document.querySelector<HTMLInputElement>("input[type='file']")!;
    fireEvent.change(fileInput(), {
      target: { files: [new File(["x"], "doc.pdf", { type: "application/pdf" })] },
    });
    await waitFor(() =>
      expect(
        document.querySelector(
          "[data-testid='mention-composer-document-tray']",
        ),
      ).not.toBeNull(),
    );

    openExpanded(getByLabelText);
    await waitFor(() => expect(expandedDialog()).not.toBeNull());
    expect(
      expandedDialog()!.querySelector(
        "[data-testid='mention-composer-document-tray']",
      ),
    ).not.toBeNull();

    fireEvent.click(
      expandedDialog()!.querySelector(
        "button[aria-label='Recolher conversa']",
      )!,
    );
    await waitFor(() => expect(expandedDialog()).toBeNull());
    expect(
      container.querySelector(
        "[data-testid='mention-composer-document-tray']",
      ),
    ).not.toBeNull();
  });
});
