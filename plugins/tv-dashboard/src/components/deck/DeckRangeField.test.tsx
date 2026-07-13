import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DeckRangeField } from "./DeckRangeField";

afterEach(() => {
  cleanup();
});

describe("DeckRangeField", () => {
  it("mantém o input numérico depois do slider no DOM (layout base)", () => {
    render(
      <DeckRangeField id="td-layout" label="Larg. px" value={10} min={0} max={100} onChange={() => undefined} />,
    );
    const slider = screen.getByLabelText("Larg. px");
    const input = screen.getByLabelText("Larg. px (digitar)");
    const row = slider.closest(".td-deck-ribbon__range-row");
    expect(row).toBeTruthy();
    expect(row!.contains(slider)).toBe(true);
    expect(row!.contains(input)).toBe(true);
    expect(
      Boolean(slider.compareDocumentPosition(input) & Node.DOCUMENT_POSITION_FOLLOWING),
    ).toBe(true);
  });

  it("permite digitar o valor no input numérico", () => {
    const onChange = vi.fn();
    render(
      <DeckRangeField
        id="td-x"
        label="X px"
        value={100}
        min={0}
        max={1920}
        onChange={onChange}
      />,
    );
    const input = screen.getByLabelText("X px (digitar)");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "250.5" } });
    fireEvent.blur(input);
    expect(onChange).toHaveBeenCalledWith(250.5);
  });

  it("slider continua aplicando valor", () => {
    const onChange = vi.fn();
    render(
      <DeckRangeField id="td-y" label="Y px" value={10} min={0} max={100} onChange={onChange} />,
    );
    fireEvent.change(screen.getByLabelText("Y px"), { target: { value: "42" } });
    expect(onChange).toHaveBeenCalledWith(42);
  });

  it("exibe e aceita displayValue com sufixo % (opacidade)", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <DeckRangeField
        id="td-opacity"
        label="Opacidade"
        value={80}
        min={0}
        max={100}
        step={5}
        displayValue="80%"
        onChange={onChange}
      />,
    );
    const input = screen.getByLabelText("Opacidade (digitar)") as HTMLInputElement;
    expect(input.value).toBe("80%");

    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "55%" } });
    fireEvent.blur(input);
    expect(onChange).toHaveBeenCalledWith(55);

    rerender(
      <DeckRangeField
        id="td-opacity"
        label="Opacidade"
        value={55}
        min={0}
        max={100}
        step={5}
        displayValue="55%"
        onChange={onChange}
      />,
    );
    expect((screen.getByLabelText("Opacidade (digitar)") as HTMLInputElement).value).toBe("55%");
  });
});
