import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ConversationUserMessage } from "./ConversationUserMessage";

afterEach(cleanup);

describe("ConversationUserMessage", () => {
  it("renders plain text verbatim, including newlines and unsafe markup as text", () => {
    const content = "Linha 1\nLinha 2 <script>alert('x')</script> & pronto";
    const { container } = render(
      <ConversationUserMessage authorLabel="Você">{content}</ConversationUserMessage>,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-user-message__content")?.textContent,
    ).toBe(content);
    expect(container.querySelector("script")).toBeNull();
    expect(screen.getByText("Você")).toBeTruthy();
  });

  it("accepts presentational content as a slot without interpreting it", () => {
    render(
      <ConversationUserMessage>
        <strong data-testid="custom-content">Conteúdo explícito</strong>
      </ConversationUserMessage>,
    );
    expect(screen.getByTestId("custom-content").textContent).toBe("Conteúdo explícito");
  });

  it("shows an avatar slot and hides duplicate avatar semantics when the author is visible", () => {
    const { container } = render(
      <ConversationUserMessage
        authorLabel="Você"
        avatar={<span role="img" aria-label="Avatar">A</span>}
      >
        Pergunta
      </ConversationUserMessage>,
    );
    const wrapper = container.querySelector(".delpi-ui-conversation-user-message__avatar");
    expect(wrapper?.getAttribute("aria-hidden")).toBe("true");
    expect(wrapper?.textContent).toBe("A");
  });

  it("keeps avatar semantics when no visible author is supplied", () => {
    const { container } = render(
      <ConversationUserMessage avatar={<span role="img" aria-label="Pessoa">A</span>}>
        Texto
      </ConversationUserMessage>,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-user-message__avatar")?.hasAttribute("aria-hidden"),
    ).toBe(false);
    expect(container.querySelector(".delpi-ui-conversation-user-message__author")).toBeNull();
  });

  it("omits optional avatar and author safely", () => {
    const { container } = render(<ConversationUserMessage>Texto</ConversationUserMessage>);
    expect(container.querySelector(".delpi-ui-conversation-user-message__avatar")).toBeNull();
    expect(container.querySelector(".delpi-ui-conversation-user-message__author")).toBeNull();
    expect(container.textContent).toBe("Texto");
  });

  it("supports compact density and caller-owned class hooks", () => {
    const { container } = render(
      <ConversationUserMessage density="compact" className="host-message" contentClassName="host-content">
        Texto longo sem espaços: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      </ConversationUserMessage>,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-user-message--compact.host-message"),
    ).toBeTruthy();
    expect(
      container.querySelector(".delpi-ui-conversation-user-message__content.host-content"),
    ).toBeTruthy();
  });

  it("does not introduce a nested live region, alert, status or focusable wrapper", () => {
    const { container } = render(
      <ConversationUserMessage authorLabel="Você">Pergunta</ConversationUserMessage>,
    );
    const root = container.querySelector(".delpi-ui-conversation-user-message");
    expect(root?.hasAttribute("role")).toBe(false);
    expect(root?.hasAttribute("aria-live")).toBe(false);
    expect(root?.hasAttribute("tabindex")).toBe(false);
    expect(container.querySelector('[role="log"], [role="alert"], [role="status"]')).toBeNull();
  });
});
