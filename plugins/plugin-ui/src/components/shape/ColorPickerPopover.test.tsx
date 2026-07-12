import { describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach } from "vitest";

import { ColorPickerPopover } from "./ColorPickerPopover";

afterEach(() => {
  cleanup();
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

  it("mostra Automático no variant text e escolhe contraste", () => {
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
    expect(onChange).toHaveBeenCalledWith("#ffffff");
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
});
