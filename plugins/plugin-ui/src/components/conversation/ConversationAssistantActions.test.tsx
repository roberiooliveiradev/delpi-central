import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConversationAssistantActions } from "./ConversationAssistantActions";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ConversationAssistantActions", () => {
  it("renders copy, feedback and regenerate controls", () => {
    render(<ConversationAssistantActions copyText="texto" />);
    expect(screen.getByRole("button", { name: "Copiar resposta" })).toBeTruthy();
    expect(
      (screen.getByRole("button", { name: "Útil" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(
      (screen.getByRole("button", { name: "Não útil" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(
      (screen.getByRole("button", { name: "Refazer resposta" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(screen.queryByRole("button", { name: "Mais opções" })).toBeNull();
  });

  it("hides more options when there are no contextual actions", () => {
    render(<ConversationAssistantActions copyText="x" moreActions={[]} />);
    expect(screen.queryByRole("button", { name: "Mais opções" })).toBeNull();
  });

  it("copies text and shows success only after clipboard resolves", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
    render(<ConversationAssistantActions copyText="copiar isto" />);
    fireEvent.click(screen.getByRole("button", { name: "Copiar resposta" }));
    expect(writeText).toHaveBeenCalledWith("copiar isto");
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Resposta copiada" })).toBeTruthy(),
    );
  });

  it("does not claim success when clipboard rejects", async () => {
    const writeText = vi.fn().mockRejectedValue(new Error("denied"));
    const onCopyError = vi.fn();
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
    render(
      <ConversationAssistantActions
        copyText="x"
        onCopyError={onCopyError}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Copiar resposta" }));
    await waitFor(() => expect(onCopyError).toHaveBeenCalled());
    expect(screen.getByRole("button", { name: "Copiar resposta" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Resposta copiada" })).toBeNull();
  });

  it("toggles mutually exclusive feedback when enabled", () => {
    const onFeedbackChange = vi.fn();
    const { rerender } = render(
      <ConversationAssistantActions
        copyText="x"
        feedbackEnabled
        feedbackValue={null}
        onFeedbackChange={onFeedbackChange}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Útil" }));
    expect(onFeedbackChange).toHaveBeenCalledWith("positive");

    rerender(
      <ConversationAssistantActions
        copyText="x"
        feedbackEnabled
        feedbackValue="positive"
        onFeedbackChange={onFeedbackChange}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Útil" }).getAttribute("aria-pressed"),
    ).toBe("true");
    fireEvent.click(screen.getByRole("button", { name: "Não útil" }));
    expect(onFeedbackChange).toHaveBeenCalledWith("negative");
  });

  it("does not fire feedback without callback even if enabled flag is set", () => {
    render(
      <ConversationAssistantActions
        copyText="x"
        feedbackEnabled
      />,
    );
    expect(
      (screen.getByRole("button", { name: "Útil" }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });

  it("invokes regenerate only when enabled with callback", () => {

    const onRegenerate = vi.fn();
    render(
      <ConversationAssistantActions
        copyText="x"
        regenerateEnabled
        onRegenerate={onRegenerate}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Refazer resposta" }));
    expect(onRegenerate).toHaveBeenCalledTimes(1);
  });

  it("opens more menu only for real actions and invokes selection", () => {
    const onSelect = vi.fn();
    render(
      <ConversationAssistantActions
        copyText="x"
        moreActions={[{ id: "export", label: "Exportar", onSelect }]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Mais opções" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Exportar" }));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("exposes an accessible group label and keeps controls keyboard focusable", () => {
    render(<ConversationAssistantActions copyText="x" />);
    const group = screen.getByRole("group", { name: "Ações da resposta" });
    expect(group).toBeTruthy();
    const copy = screen.getByRole("button", { name: "Copiar resposta" });
    copy.focus();
    expect(document.activeElement).toBe(copy);
  });

  it("disables the strip when loading or disabled", () => {
    render(
      <ConversationAssistantActions
        copyText="x"
        loading
        feedbackEnabled
        onFeedbackChange={() => {}}
        regenerateEnabled
        onRegenerate={() => {}}
      />,
    );
    expect(
      (screen.getByRole("button", { name: "Copiar resposta" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(
      (screen.getByRole("button", { name: "Útil" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(
      (screen.getByRole("button", { name: "Refazer resposta" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });
});
