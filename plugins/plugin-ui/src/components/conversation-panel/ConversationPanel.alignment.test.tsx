/** P3-FIX RQ-02/RQ-03 — o painel compartilhado deve derivar o
 * alinhamento exclusivamente do `isMine` do contrato e renderizar
 * toda mensagem (própria ou recebida) como bolha completa com
 * identidade. */

import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ConversationPanel } from "./ConversationPanel";
import type {
  ConversationApi,
  ConversationComment,
} from "./ConversationPanel";

afterEach(() => {
  cleanup();
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

describe("ConversationPanel — alinhamento e bolhas (P3-FIX)", () => {
  it("isMine=true gera item/bubble mine; recebida gera bolha comum com autor e avatar", async () => {
    const { container } = render(
      <ConversationPanel
        requestId="req-1"
        api={apiOf([
          comment({ id: "c-1", authorName: "Bruno Costa", isMine: false }),
          comment({ id: "c-2", authorName: "Eu Mesmo", isMine: true }),
        ])}
        canComment
      />,
    );

    await waitFor(() =>
      expect(
        container.querySelectorAll(".delpi-ui-message-thread__item").length,
      ).toBe(2),
    );

    const mineItem = container.querySelector(
      ".delpi-ui-message-thread__item--mine",
    );
    expect(mineItem).not.toBeNull();
    expect(
      mineItem!.querySelector(".delpi-ui-message-thread__bubble--mine"),
    ).not.toBeNull();
    // showMineIdentity: autor e avatar visíveis também nas próprias.
    expect(mineItem!.textContent).toContain("Eu Mesmo");
    expect(
      mineItem!.querySelector(".delpi-ui-avatar"),
    ).not.toBeNull();

    const receivedItem = container.querySelector(
      '[data-message-id="c-1"]',
    )!;
    expect(receivedItem.classList.contains("delpi-ui-message-thread__item--mine")).toBe(
      false,
    );
    // Toda mensagem recebida é uma bolha completa — nunca texto solto.
    const bubble = receivedItem.querySelector(
      ".delpi-ui-message-thread__bubble",
    );
    expect(bubble).not.toBeNull();
    expect(
      bubble!.classList.contains("delpi-ui-message-thread__bubble--mine"),
    ).toBe(false);
    expect(receivedItem.textContent).toContain("Bruno Costa");
    expect(
      receivedItem.querySelector(".delpi-ui-avatar"),
    ).not.toBeNull();
    expect(receivedItem.querySelector("time")).not.toBeNull();
  });

  it("mesmo requestId, identidades opostas invertem o alinhamento", async () => {
    const items = [
      comment({ id: "c-1", authorName: "Ana", isMine: false }),
      comment({ id: "c-2", authorName: "Beto", isMine: true }),
    ];
    const swapped = items.map((item) => ({
      ...item,
      isMine: !item.isMine,
    }));

    const first = render(
      <ConversationPanel requestId="req-1" api={apiOf(items)} canComment />,
    );
    await waitFor(() =>
      expect(
        first.container.querySelectorAll(
          ".delpi-ui-message-thread__item--mine",
        ).length,
      ).toBe(1),
    );
    const firstMineId = first.container
      .querySelector(".delpi-ui-message-thread__item--mine")
      ?.getAttribute("data-message-id");
    cleanup();

    const second = render(
      <ConversationPanel requestId="req-1" api={apiOf(swapped)} canComment />,
    );
    await waitFor(() =>
      expect(
        second.container.querySelectorAll(
          ".delpi-ui-message-thread__item--mine",
        ).length,
      ).toBe(1),
    );
    const secondMineId = second.container
      .querySelector(".delpi-ui-message-thread__item--mine")
      ?.getAttribute("data-message-id");

    // O lado depende só de isMine — não do autor nem da ordem.
    expect(firstMineId).not.toBe(secondMineId);
  });
});
