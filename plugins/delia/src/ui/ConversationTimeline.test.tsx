import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConversationTimeline } from "./ConversationTimeline";

afterEach(cleanup);

const onConfirmation = () => {};

describe("ConversationTimeline — shared user message", () => {
  it("preserves log ownership, order, literal multiline text and assistant rendering", () => {
    const original = "Primeira linha\nSegunda linha <script>sem executar</script>";
    const { container } = render(
      <ConversationTimeline
        loading={false}
        onConfirmation={onConfirmation}
        turns={[
          { id: "u1", role: "user", content: original },
          { id: "d1", role: "delia", content: "Resposta DÉLIA" },
          { id: "u2", role: "user", content: "Outra pergunta" },
        ]}
      />,
    );
    const log = screen.getByRole("log", { name: "Conversa atual" });
    expect(log.children).toHaveLength(3);
    expect(log.children[0].querySelector(".delpi-ui-conversation-user-message")).toBeTruthy();
    expect(log.children[1].querySelector(".delia-turn--delia")).toBeNull();
    expect(log.children[1].querySelector(".delia-turn__content")?.textContent).toBe("Resposta DÉLIA");
    expect(log.children[2].querySelector(".delpi-ui-conversation-user-message")).toBeTruthy();
    const content = log.children[0].querySelector(".delpi-ui-conversation-user-message__content");
    expect(content?.textContent).toBe(original);
    expect(container.querySelector("script")).toBeNull();
    expect(log.children[0].querySelector(".delpi-ui-conversation-user-message__author")?.textContent).toBe("Você");
    expect(log.querySelectorAll('[role="log"]')).toHaveLength(0);
  });

  it("preserves published identity (photo and name fallback) without new fetches", () => {
    const { container, rerender } = render(
      <ConversationTimeline
        loading={false}
        onConfirmation={onConfirmation}
        turns={[{ id: "u1", role: "user", content: "Pergunta" }]}
        userIdentity={{ displayName: "Ana Lima", imageUrl: "blob:https://host/p" }}
      />,
    );
    expect(container.querySelector(".delpi-ui-conversation-user-message__avatar img")?.getAttribute("src")).toBe("blob:https://host/p");
    rerender(
      <ConversationTimeline
        loading={false}
        onConfirmation={onConfirmation}
        turns={[{ id: "u1", role: "user", content: "Pergunta" }]}
        userIdentity={{ displayName: "Ana Lima", imageUrl: null }}
      />,
    );
    expect(container.querySelector(".delpi-ui-unified-avatar--person")?.textContent).toContain("AL");
    expect(container.querySelector(".delpi-ui-conversation-user-message__avatar img")).toBeNull();
  });

  it("keeps the neutral user avatar when no identity was published", () => {
    const { container } = render(
      <ConversationTimeline
        loading={false}
        onConfirmation={onConfirmation}
        turns={[{ id: "u1", role: "user", content: "Pergunta" }]}
      />,
    );
    expect(container.querySelector(".delpi-ui-unified-avatar--person")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-conversation-user-message__avatar img")).toBeNull();
    expect(container.querySelector(".delpi-ui-conversation-user-message__author")?.textContent).toBe("Você");
  });

  it("exposes a discrete copy action bound to the literal user text", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText },
    });
    const { container } = render(
      <ConversationTimeline
        loading={false}
        onConfirmation={onConfirmation}
        turns={[{ id: "u1", role: "user", content: "Texto literal do usuário" }]}
      />,
    );
    expect(
      container.querySelector(
        ".delpi-ui-conversation-user-message.delpi-ui-message-action-scope",
      ),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Copiar mensagem" }));
    expect(writeText).toHaveBeenCalledWith("Texto literal do usuário");
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Mensagem copiada" }),
      ).toBeTruthy(),
    );
  });

  it("does not render edit, resend or delete affordances on user turns", () => {
    const { container } = render(
      <ConversationTimeline
        loading={false}
        onConfirmation={onConfirmation}
        turns={[{ id: "u1", role: "user", content: "Pergunta" }]}
      />,
    );
    const message = container.querySelector(
      ".delpi-ui-conversation-user-message",
    );
    const labels = ["Editar", "Reenviar", "Excluir"];
    for (const label of labels) {
      expect(
        message?.querySelector(`[aria-label*="${label}"]`),
      ).toBeNull();
    }
  });
});
