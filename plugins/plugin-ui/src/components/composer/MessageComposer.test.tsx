import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { IconButton } from "../actions/IconButton";
import { MessageComposer } from "./MessageComposer";

function renderComposer(
  overrides: Partial<Parameters<typeof MessageComposer>[0]> = {},
) {
  const onChange = vi.fn();
  const onSubmit = vi.fn();
  const view = render(
    <MessageComposer
      value=""
      onChange={onChange}
      onSubmit={onSubmit}
      inputLabel="Pergunte"
      {...overrides}
    />,
  );
  return { ...view, onChange, onSubmit };
}

afterEach(cleanup);

describe("MessageComposer — surface e escrita", () => {
  it("renders single surface with textarea and send control", () => {
    const { container } = renderComposer({ placeholder: "Pergunte…" });
    expect(container.querySelectorAll(".delpi-ui-message-composer__surface"))
      .toHaveLength(1);
    expect(screen.getByLabelText("Pergunte")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeTruthy();
    // Textarea has no inner frame of its own.
    const input = container.querySelector(
      "textarea.delpi-ui-message-composer__input",
    ) as HTMLElement;
    expect(input.className).not.toContain("card");
  });

  it("typing propagates value changes", () => {
    const { onChange } = renderComposer();
    fireEvent.change(screen.getByLabelText("Pergunte"), {
      target: { value: "olá" },
    });
    expect(onChange).toHaveBeenCalledWith("olá");
  });

  it("Enter submits when there is content", () => {
    const { onSubmit } = renderComposer({ value: "pergunta" });
    fireEvent.keyDown(screen.getByLabelText("Pergunte"), { key: "Enter" });
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("Shift+Enter inserts newline instead of submitting", () => {
    const { onSubmit } = renderComposer({ value: "linha" });
    fireEvent.keyDown(screen.getByLabelText("Pergunte"), {
      key: "Enter",
      shiftKey: true,
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("IME composition Enter never submits", () => {
    const { onSubmit } = renderComposer({ value: "日文" });
    fireEvent.keyDown(screen.getByLabelText("Pergunte"), {
      key: "Enter",
      isComposing: true,
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("empty or blank submit is blocked", () => {
    const { onSubmit } = renderComposer({ value: "   " });
    fireEvent.keyDown(screen.getByLabelText("Pergunte"), { key: "Enter" });
    expect(onSubmit).not.toHaveBeenCalled();
    expect(
      (screen.getByRole("button", { name: "Enviar" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });

  it("disabled state blocks textarea and submit", () => {
    const { onSubmit } = renderComposer({ value: "x", disabled: true });
    const input = screen.getByLabelText("Pergunte") as HTMLTextAreaElement;
    expect(input.disabled).toBe(true);
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

describe("MessageComposer — toolbar", () => {
  it("renders real secondary actions in the left region only when provided", () => {
    renderComposer({
      secondaryActions: (
        <IconButton aria-label="Anexar arquivo" onClick={() => {}}>
          +
        </IconButton>
      ),
    });
    expect(screen.getByRole("button", { name: "Anexar arquivo" }))
      .toBeTruthy();
  });

  it("renders no secondary action controls by default", () => {
    renderComposer();
    // Only the send control exists.
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });

  it("shows keyboard hint text", () => {
    renderComposer();
    expect(
      screen.getByText("Enter envia · Shift+Enter quebra linha"),
    ).toBeTruthy();
  });

  it("omits the keyboard hint when null", () => {
    renderComposer({ keyboardHint: null });
    expect(screen.queryByText(/Enter envia/)).toBeNull();
  });
});

describe("MessageComposer — contador", () => {
  it("renders counter only with a contracted limit", () => {
    const { unmount } = renderComposer({ value: "abc", characterLimit: 16384 });
    expect(screen.getByText("3/16384")).toBeTruthy();
    unmount();
    renderComposer({ value: "abc" });
    expect(screen.queryByText(/\/16384/)).toBeNull();
  });
});

describe("MessageComposer — send button", () => {
  it("loading disables send and announces indeterminate progress", () => {
    renderComposer({ value: "x", loading: true });
    const send = screen.getByRole("button", {
      name: "Enviando…",
    }) as HTMLButtonElement;
    expect(send.disabled).toBe(true);
    // Textarea is also gated while sending.
    expect(
      (screen.getByLabelText("Pergunte") as HTMLTextAreaElement).disabled,
    ).toBe(true);
  });

  it("send click submits once and only via explicit intent", () => {
    const { onSubmit } = renderComposer({ value: "pergunta real" });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});

describe("MessageComposer — helper e erro", () => {
  it("renders helper text outside the surface", () => {
    const { container } = renderComposer({
      helperText: "Confirme informações importantes.",
    });
    const helper = screen.getByText("Confirme informações importantes.");
    expect(helper.className).toContain("delpi-ui-message-composer__helper");
    expect(helper.closest(".delpi-ui-message-composer__surface")).toBeNull();
  });

  it("renders error with role=alert and keeps the draft", () => {
    renderComposer({ value: "rascunho", error: "falha ao enviar" });
    expect(screen.getByRole("alert").textContent).toContain(
      "falha ao enviar",
    );
    expect(
      (screen.getByLabelText("Pergunte") as HTMLTextAreaElement).value,
    ).toBe("rascunho");
  });
});
