import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
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

  it("CSS do stepper não estica o combobox no host (.td-field)", () => {
    const css = readFileSync(
      resolve(dirname(fileURLToPath(import.meta.url)), "../../styles/number-stepper.css"),
      "utf8",
    );
    expect(css).toMatch(/width:\s*max-content/);
    expect(css).toMatch(
      /\.delpi-ui-number-stepper \.delpi-ui-combobox-number \{[\s\S]*?flex:\s*0 0 auto/,
    );
    expect(css).toMatch(
      /\.delpi-ui-number-stepper \.delpi-ui-combobox-number__toggle \{[\s\S]*?width:\s*22px/,
    );
  });

  it("CSS centraliza ícones − / chevron / + (sem stretch no wrapper)", () => {
    const css = readFileSync(
      resolve(dirname(fileURLToPath(import.meta.url)), "../../styles/number-stepper.css"),
      "utf8",
    );
    // Regressão: `> * { align-items: stretch }` esticava SVG Lucide e desalinhava ícones.
    expect(css).toMatch(
      /\.delpi-ui-number-stepper > \* \{[\s\S]*?align-items:\s*center/,
    );
    expect(css).toMatch(
      /\.delpi-ui-number-stepper__step \{[\s\S]*?line-height:\s*0/,
    );
    expect(css).toMatch(
      /\.delpi-ui-number-stepper__step svg \{[\s\S]*?display:\s*block/,
    );
    expect(css).toMatch(
      /\.delpi-ui-number-stepper \.delpi-ui-combobox-number__toggle svg \{[\s\S]*?display:\s*block/,
    );
  });
});
