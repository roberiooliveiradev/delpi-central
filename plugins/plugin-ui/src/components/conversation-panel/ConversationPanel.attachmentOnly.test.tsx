/** P3-FIX-03 — envio de mensagem composta só por anexos (Issue #207).
 * Contrato: nunca corpo artificial (" "); a criação composta vai numa
 * única chamada `createCommentWithAttachments` com `body:""` canônico.
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  ConversationPanel,
  type ConversationApi,
  type ConversationAttachmentFile,
  type ConversationComment,
} from "./ConversationPanel";

beforeAll(() => {
  // jsdom não implementa blob URLs — o strip de pendentes cria um
  // objectURL por imagem; stub suficiente para o ciclo do teste.
  URL.createObjectURL = vi.fn(() => "blob:mock");
  URL.revokeObjectURL = vi.fn();
});

afterEach(cleanup);

const comment = (
  partial: Partial<ConversationComment> = {},
): ConversationComment => ({
  id: "c-1",
  requestId: "req-1",
  authorId: "u-1",
  authorName: "Ana",
  body: "oi",
  version: 1,
  isMine: true,
  createdAt: "2026-01-01T10:00:00Z",
  updatedAt: "2026-01-01T10:00:00Z",
  edited: false,
  ...partial,
});

function apiOf(overrides: Partial<ConversationApi> = {}) {
  const createComment = vi.fn(
    async (
      _requestId: string,
      _body: string,
      _opts?: { idempotencyKey?: string },
    ) => comment({ id: "created" }),
  );
  const createCommentWithAttachments = vi.fn(
    async (
      _requestId: string,
      _input: { body: string; files: ConversationAttachmentFile[] },
      _opts?: { idempotencyKey?: string },
    ) => ({
    comment: comment({ id: "created", body: "" }),
    attachments: [
      {
        id: "a-1",
        fileName: "print.png",
        mediaType: "image/png",
        sizeBytes: 4,
        clientRef: null,
      },
    ],
    }),
  );
  const api: ConversationApi = {
    listComments: async () => [],
    createComment,
    createCommentWithAttachments,
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
    ...overrides,
  };
  return { api, createComment, createCommentWithAttachments };
}

const PNG_FILE = () =>
  new File([new Uint8Array([0x89, 0x50, 0x4e, 0x47])], "print.png", {
    type: "image/png",
  });

const PDF_FILE = () =>
  new File([new Uint8Array([0x25, 0x50, 0x44, 0x46])], "doc.pdf", {
    type: "application/pdf",
  });

async function attachFile(
  container: HTMLElement,
  file: File,
): Promise<void> {
  const input = container.querySelector<HTMLInputElement>(
    "input[type=file]",
  );
  expect(input).not.toBeNull();
  fireEvent.change(input!, { target: { files: [file] } });
  await waitFor(() =>
    expect(
      container.querySelector(
        "[data-testid='mention-composer-document-tray'], " +
          "[data-testid='mention-composer-image-thumbs']",
      ),
    ).not.toBeNull(),
  );
}

function submit(container: HTMLElement): void {
  const surface = container.querySelector<HTMLElement>(
    "[role='textbox']",
  );
  expect(surface).not.toBeNull();
  fireEvent.keyDown(surface!, { key: "Enter" });
}

describe("ConversationPanel — envio só-anexo (P3-FIX-03)", () => {
  it("imagem sem texto chama createCommentWithAttachments com body vazio — nunca ' '", async () => {
    const { api, createComment, createCommentWithAttachments } = apiOf();
    const { container } = render(
      <ConversationPanel requestId="req-1" api={api} canComment />,
    );
    await attachFile(container, PNG_FILE());
    submit(container);
    await waitFor(() =>
      expect(createCommentWithAttachments).toHaveBeenCalledTimes(1),
    );
    const [requestId, input, opts] =
      createCommentWithAttachments.mock.calls[0];
    expect(requestId).toBe("req-1");
    expect(input.body).toBe(""); // canônico — nunca espaço artificial
    expect(input.files).toHaveLength(1);
    expect(input.files[0].file.name).toBe("print.png");
    expect(createComment).not.toHaveBeenCalled();
    expect(String(opts?.idempotencyKey || "")).not.toBe("");
  });

  it("PDF sem texto passa pela mesma criação composta", async () => {
    const { api, createComment, createCommentWithAttachments } = apiOf();
    const { container } = render(
      <ConversationPanel requestId="req-1" api={api} canComment />,
    );
    await attachFile(container, PDF_FILE());
    submit(container);
    await waitFor(() =>
      expect(createCommentWithAttachments).toHaveBeenCalledTimes(1),
    );
    expect(createCommentWithAttachments.mock.calls[0][1].body).toBe("");
  });

  it("múltiplos anexos sem texto vão na mesma chamada", async () => {
    const { api, createComment, createCommentWithAttachments } = apiOf();
    const { container } = render(
      <ConversationPanel requestId="req-1" api={api} canComment />,
    );
    await attachFile(container, PNG_FILE());
    const input = container.querySelector<HTMLInputElement>(
      "input[type=file]",
    )!;
    fireEvent.change(input, { target: { files: [PDF_FILE()] } });
    await waitFor(() => {
      const tray = container.querySelector(
        "[data-testid='mention-composer-document-tray']",
      );
      const thumbs = container.querySelector(
        "[data-testid='mention-composer-image-thumbs']",
      );
      expect(
        (tray?.textContent || "") + (thumbs?.textContent || ""),
      ).toContain("doc.pdf");
    });
    submit(container);
    await waitFor(() =>
      expect(createCommentWithAttachments).toHaveBeenCalledTimes(1),
    );
    expect(
      createCommentWithAttachments.mock.calls[0][1].files,
    ).toHaveLength(2);
  });

  it("texto + anexo também usa a criação composta", async () => {
    const { api, createComment, createCommentWithAttachments } = apiOf();
    const { container } = render(
      <ConversationPanel requestId="req-1" api={api} canComment />,
    );
    await attachFile(container, PNG_FILE());
    const surface = container.querySelector<HTMLElement>(
      "[role='textbox']",
    )!;
    surface.innerHTML = "<p>segue o print</p>";
    fireEvent.input(surface);
    submit(container);
    await waitFor(() =>
      expect(createCommentWithAttachments).toHaveBeenCalledTimes(1),
    );
    const input = createCommentWithAttachments.mock.calls[0][1];
    expect(input.body).toContain("segue o print");
    expect(input.files).toHaveLength(1);
    expect(createComment).not.toHaveBeenCalled();
  });

  it("texto puro continua no createComment legado (JSON)", async () => {
    const { api, createComment, createCommentWithAttachments } = apiOf();
    const { container } = render(
      <ConversationPanel requestId="req-1" api={api} canComment />,
    );
    const surface = container.querySelector<HTMLElement>(
      "[role='textbox']",
    )!;
    surface.innerHTML = "<p>só texto</p>";
    fireEvent.input(surface);
    submit(container);
    await waitFor(() =>
      expect(createComment).toHaveBeenCalledTimes(1),
    );
    expect(createComment.mock.calls[0][1]).toBe("só texto");
    expect(createCommentWithAttachments).not.toHaveBeenCalled();
  });

  it("sem texto e sem anexo nada é enviado", async () => {
    const { api, createComment, createCommentWithAttachments } = apiOf();
    const { container } = render(
      <ConversationPanel requestId="req-1" api={api} canComment />,
    );
    submit(container);
    await new Promise((r) => setTimeout(r, 50));
    expect(createComment).not.toHaveBeenCalled();
    expect(createCommentWithAttachments).not.toHaveBeenCalled();
  });
});
