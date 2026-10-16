import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConversationError } from "./ConversationError";

afterEach(cleanup);

describe("ConversationError", () => {
  it("renders title in a single alert region", () => {
    const { container } = render(
      <ConversationError title="Não foi possível concluir esta solicitação." />,
    );
    const alerts = container.querySelectorAll('[role="alert"]');
    expect(alerts.length).toBe(1);
    expect(
      screen.getByText("Não foi possível concluir esta solicitação."),
    ).toBeTruthy();
  });

  it("renders optional description and omits it when absent", () => {
    const { container, rerender } = render(
      <ConversationError title="t" description="Sua mensagem foi preservada." />,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-error__description"),
    ).toBeTruthy();
    rerender(<ConversationError title="t" />);
    expect(
      container.querySelector(".delpi-ui-conversation-error__description"),
    ).toBeNull();
  });

  it("icon slot is decorative (aria-hidden)", () => {
    const { container } = render(<ConversationError title="t" />);
    const icon = container.querySelector(".delpi-ui-conversation-error__icon");
    expect(icon?.getAttribute("aria-hidden")).toBe("true");
  });

  it("renders action only with both label and callback", () => {
    const { queryByRole, rerender } = render(
      <ConversationError title="t" actionLabel="Tentar novamente" />,
    );
    expect(queryByRole("button")).toBeNull();
    rerender(<ConversationError title="t" onAction={() => {}} />);
    expect(queryByRole("button")).toBeNull();
  });

  it("fires onAction and honors disabled/loading", () => {
    const onAction = vi.fn();
    const { rerender } = render(
      <ConversationError
        title="t"
        actionLabel="Tentar novamente"
        onAction={onAction}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(onAction).toHaveBeenCalledTimes(1);

    rerender(
      <ConversationError
        title="t"
        actionLabel="Tentar novamente"
        onAction={onAction}
        loading
      />,
    );
    const btn = screen.getByRole("button", { name: "Tentar novamente" });
    expect(btn.hasAttribute("disabled")).toBe(true);
    fireEvent.click(btn);
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("supports compact density and className", () => {
    const { container } = render(
      <ConversationError title="t" density="compact" className="mine" />,
    );
    const root = container.querySelector(".delpi-ui-conversation-error")!;
    expect(
      root.classList.contains("delpi-ui-conversation-error--compact"),
    ).toBe(true);
    expect(root.classList.contains("mine")).toBe(true);
  });

  it("keeps hostile copy inert (text, never markup)", () => {
    const hostile = "<img src=x onerror=alert(1)>Bearer abc";
    render(<ConversationError title={hostile} />);
    expect(screen.getByText(hostile)).toBeTruthy();
    expect(document.querySelector("img")).toBeNull();
  });
});
