import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConversationScrollNavigator } from "./ConversationScrollNavigator";

afterEach(cleanup);

describe("ConversationScrollNavigator", () => {
  it("is absent when not visible", () => {
    render(<ConversationScrollNavigator visible={false} onGoToLatest={() => {}} />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("invokes the supplied callback only from an explicit click", () => {
    const go = vi.fn();
    const { rerender } = render(
      <ConversationScrollNavigator visible onGoToLatest={go} />,
    );
    const button = screen.getByRole("button", { name: "Ir para o final da conversa" });
    expect(button.getAttribute("type")).toBe("button");
    button.focus();
    expect(document.activeElement).toBe(button);
    fireEvent.click(button);
    expect(go).toHaveBeenCalledTimes(1);
    rerender(<ConversationScrollNavigator visible onGoToLatest={go} disabled />);
    fireEvent.click(screen.getByRole("button"));
    expect(go).toHaveBeenCalledTimes(1);
  });

  it("supports an accessible custom label", () => {
    render(<ConversationScrollNavigator visible onGoToLatest={() => {}} label="Ver novas mensagens" />);
    expect(screen.getByRole("button", { name: "Ver novas mensagens" })).toBeTruthy();
  });
});
