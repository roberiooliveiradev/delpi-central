import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ConversationStatus } from "./ConversationStatus";

afterEach(cleanup);

describe("ConversationStatus", () => {
  it("renders the label through the canonical StatusBadge", () => {
    const { container } = render(
      <ConversationStatus label="Confirmação pendente" tone="warning" />,
    );
    const badge = container.querySelector(".delpi-ui-status-badge")!;
    expect(badge.textContent).toBe("Confirmação pendente");
    expect(badge.classList.contains("delpi-ui-status-badge--warning")).toBe(true);
  });

  it("applies tone class on the root", () => {
    const { container } = render(
      <ConversationStatus label="x" tone="danger" />,
    );
    const root = container.querySelector(".delpi-ui-conversation-status")!;
    expect(root.classList.contains("delpi-ui-conversation-status--danger")).toBe(
      true,
    );
  });

  it("renders a decorative icon slot (aria-hidden)", () => {
    const { container } = render(
      <ConversationStatus label="x" icon={<svg data-testid="i" />} />,
    );
    const slot = container.querySelector(
      ".delpi-ui-conversation-status__icon",
    )!;
    expect(slot.getAttribute("aria-hidden")).toBe("true");
    expect(slot.querySelector("svg")).toBeTruthy();
  });

  it("omits the icon slot when no icon is given", () => {
    const { container } = render(<ConversationStatus label="x" />);
    expect(
      container.querySelector(".delpi-ui-conversation-status__icon"),
    ).toBeNull();
  });

  it("supports optional description, density compact and className", () => {
    const { container } = render(
      <ConversationStatus
        label="x"
        description="detalhe extra"
        density="compact"
        className="mine"
      />,
    );
    const root = container.querySelector(".delpi-ui-conversation-status")!;
    expect(root.classList.contains("delpi-ui-conversation-status--compact")).toBe(
      true,
    );
    expect(root.classList.contains("mine")).toBe(true);
    expect(
      container.querySelector(".delpi-ui-conversation-status__description")!
        .textContent,
    ).toBe("detalhe extra");
  });

  it("has no live-region role by default; group name only when labeled", () => {
    const { container } = render(<ConversationStatus label="x" />);
    const root = container.querySelector(".delpi-ui-conversation-status")!;
    expect(root.getAttribute("role")).toBeNull();

    const { container: labeled } = render(
      <ConversationStatus label="x" aria-label="Estado da resposta" />,
    );
    const g = labeled.querySelector(".delpi-ui-conversation-status")!;
    expect(g.getAttribute("role")).toBe("group");
    expect(g.getAttribute("aria-label")).toBe("Estado da resposta");
  });
});
