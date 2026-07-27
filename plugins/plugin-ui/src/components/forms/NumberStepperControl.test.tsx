import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NumberStepperControl } from "./NumberStepperControl";

afterEach(() => {
  cleanup();
});

describe("NumberStepperControl", () => {
  it("renderiza grupo unificado e dispara step down/up", () => {
    const onChange = vi.fn();
    const onStepDown = vi.fn();
    const onStepUp = vi.fn();
    render(
      <NumberStepperControl
        value={16}
        options={[12, 16, 24]}
        aria-label="Tamanho"
        groupAriaLabel="Tamanho da fonte"
        onChange={onChange}
        onStepDown={onStepDown}
        onStepUp={onStepUp}
        stepDownAriaLabel="Diminuir"
        stepUpAriaLabel="Aumentar"
      />,
    );

    expect(screen.getByRole("group", { name: "Tamanho da fonte" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Diminuir" }));
    fireEvent.click(screen.getByRole("button", { name: "Aumentar" }));
    expect(onStepDown).toHaveBeenCalledTimes(1);
    expect(onStepUp).toHaveBeenCalledTimes(1);
  });

  it("respeita stepDownDisabled", () => {
    const onStepDown = vi.fn();
    render(
      <NumberStepperControl
        value={12}
        options={[12, 16]}
        aria-label="Tamanho"
        onChange={vi.fn()}
        onStepDown={onStepDown}
        onStepUp={vi.fn()}
        stepDownDisabled
        stepDownAriaLabel="Diminuir"
        stepUpAriaLabel="Aumentar"
      />,
    );

    expect(
      (screen.getByRole("button", { name: "Diminuir" }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });

  it("exibe placeholder Misto sem truncar o valor vazio", () => {
    const { container } = render(
      <NumberStepperControl
        value={null}
        placeholder="Misto"
        options={[12, 16, 24]}
        aria-label="Tamanho (Misto)"
        onChange={vi.fn()}
        onStepDown={vi.fn()}
        onStepUp={vi.fn()}
        stepDownAriaLabel="Diminuir"
        stepUpAriaLabel="Aumentar"
      />,
    );
    const input = container.querySelector(
      ".delpi-ui-combobox-number__input",
    ) as HTMLInputElement | null;
    expect(input?.placeholder).toBe("Misto");
    expect(input?.value).toBe("");
  });
});
