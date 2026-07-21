import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

import { ColorPickerPopover } from "./ColorPickerPopover";
import * as eyedropper from "./pickColorWithEyedropper";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ColorPickerPopover", () => {
  it("mostra Sem fundo no variant fill e aplica transparent", () => {
    const onChange = vi.fn();
    const { container } = render(
      <ColorPickerPopover variant="fill" value="#ef4444" onChange={onChange} />,
    );
    const view = within(container);

    fireEvent.click(view.getByRole("button", { name: "Sem fundo" }));
    expect(onChange).toHaveBeenCalledWith("transparent");
  });

  it("mostra Automático no variant text e grava sentinel auto", () => {
    const onChange = vi.fn();
    const { container } = render(
      <ColorPickerPopover
        variant="text"
        value="#111111"
        contrastBackground="#0f172a"
        onChange={onChange}
      />,
    );
    const view = within(container);

    fireEvent.click(view.getByRole("button", { name: "Automático" }));
    expect(onChange).toHaveBeenCalledWith("auto");
  });

  it("mostra Sem contorno no variant outline", () => {
    const onChange = vi.fn();
    const { container } = render(
      <ColorPickerPopover variant="outline" value="#089bdb" onChange={onChange} />,
    );
    const view = within(container);

    expect(view.getByRole("button", { name: "Sem contorno" })).toBeTruthy();
    expect(view.queryByRole("button", { name: "Sem fundo" })).toBeNull();
    expect(view.queryByRole("button", { name: "Automático" })).toBeNull();
  });

  it("Mais cores abre popover (não modal) e confirma a cor", () => {
    const onChange = vi.fn();
    render(<ColorPickerPopover variant="fill" value="#089bdb" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Mais cores…" }));
    expect(document.querySelector(".delpi-ui-color-more-popover")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-shape-dialog-overlay")).toBeNull();
    expect(screen.getByRole("dialog", { name: "Cores" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(onChange).toHaveBeenCalled();
    expect(document.querySelector(".delpi-ui-color-more-popover")).toBeNull();
  });

  it("Conta-gotas usa EyeDropper quando disponível", async () => {
    vi.spyOn(eyedropper, "isEyedropperSupported").mockReturnValue(true);
    vi.spyOn(eyedropper, "pickColorWithEyedropper").mockResolvedValue("#aabbcc");
    const onChange = vi.fn();
    render(<ColorPickerPopover variant="fill" value="#089bdb" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Conta-gotas" }));
    await waitFor(() => expect(onChange).toHaveBeenCalledWith("#aabbcc"));
  });
});
