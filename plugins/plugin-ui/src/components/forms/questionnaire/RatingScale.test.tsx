import { useState } from "react";

import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RatingScale, type RatingScaleValue } from "./RatingScale";

afterEach(cleanup);

const OPTION_LABEL = (n: number) => `${n} — significado ${n}`;
const END_LABELS = { min: "1 · Mínimo", max: "5 · Máximo" };

function baseProps(overrides: Partial<Parameters<typeof RatingScale>[0]> = {}) {
  return {
    name: "q1",
    min: 1,
    max: 5,
    value: null as RatingScaleValue,
    onChange: vi.fn(),
    optionLabel: OPTION_LABEL,
    endLabels: END_LABELS,
    ...overrides,
  };
}

describe("RatingScale", () => {
  it("grupo nativo: um radio por nota com o mesmo name; nenhum marcado sem valor", () => {
    const { container } = render(<RatingScale {...baseProps()} />);
    const radios = container.querySelectorAll<HTMLInputElement>(
      'input[type="radio"]',
    );
    expect(radios).toHaveLength(5);
    for (const radio of radios) {
      expect(radio.name).toBe("q1");
      expect(radio.checked).toBe(false);
    }
  });

  it("N/A entra no mesmo grupo e chama onChange('na'); nota chama onChange(n)", () => {
    function Harness() {
      const [value, setValue] = useState<RatingScaleValue>(null);
      return (
        <RatingScale
          {...baseProps({
            value,
            onChange: setValue,
            notApplicable: { label: "Não se aplica" },
          })}
        />
      );
    }
    const { container, getByRole } = render(<Harness />);

    fireEvent.click(getByRole("radio", { name: "4 — significado 4" }));
    expect(
      container.querySelector<HTMLInputElement>('input[value="4"]')!.checked,
    ).toBe(true);

    const na = getByRole("radio", {
      name: "Não se aplica",
    }) as HTMLInputElement;
    expect(na.name).toBe("q1");
    fireEvent.click(na);
    expect((na as HTMLInputElement).checked).toBe(true);
    expect(
      container.querySelector<HTMLInputElement>('input[value="4"]')!.checked,
    ).toBe(false);

    fireEvent.click(getByRole("radio", { name: "2 — significado 2" }));
    expect((na as HTMLInputElement).checked).toBe(false);
  });

  it("onChange recebe o número clicado", () => {
    const onChange = vi.fn();
    const { getByRole } = render(
      <RatingScale {...baseProps({ onChange })} />,
    );
    fireEvent.click(getByRole("radio", { name: "3 — significado 3" }));
    expect(onChange).toHaveBeenCalledWith(3);
  });

  it("setas movem e escolhem dentro do grupo (inclui o N/A); Enter não envia form", () => {
    const onSubmit = vi.fn((event) => event.preventDefault());
    function Harness() {
      const [value, setValue] = useState<RatingScaleValue>(2);
      return (
        <form onSubmit={onSubmit}>
          <RatingScale
            {...baseProps({
              value,
              onChange: setValue,
              notApplicable: { label: "Não se aplica" },
            })}
          />
        </form>
      );
    }
    const { container, getByRole } = render(<Harness />);
    const radios = () =>
      Array.from(
        container.querySelectorAll<HTMLInputElement>('input[type="radio"]'),
      );
    // DOM: notas 1..5 depois a pílula N/A (índices 0..5)
    const r4 = getByRole("radio", { name: "4 — significado 4" });
    (r4 as HTMLInputElement).focus();

    fireEvent.keyDown(r4, { key: "ArrowRight" });
    expect(document.activeElement).toBe(radios()[4]); // nota 5
    expect((radios()[4] as HTMLInputElement).checked).toBe(true);

    fireEvent.keyDown(document.activeElement!, { key: "ArrowRight" });
    expect(document.activeElement).toBe(radios()[5]); // N/A no ciclo
    expect((radios()[5] as HTMLInputElement).checked).toBe(true);

    fireEvent.keyDown(document.activeElement!, { key: "ArrowRight" });
    expect(document.activeElement).toBe(radios()[0]); // cicla p/ nota 1

    fireEvent.keyDown(document.activeElement!, { key: "ArrowLeft" });
    expect(document.activeElement).toBe(radios()[5]); // volta ao N/A

    fireEvent.keyDown(document.activeElement!, { key: "Enter" });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("nomes acessíveis vêm de optionLabel e de notApplicable.label", () => {
    const { getByRole } = render(
      <RatingScale
        {...baseProps({ notApplicable: { label: "Sem resposta" } })}
      />,
    );
    expect(getByRole("radio", { name: "1 — significado 1" })).toBeTruthy();
    expect(getByRole("radio", { name: "5 — significado 5" })).toBeTruthy();
    expect(getByRole("radio", { name: "Sem resposta" })).toBeTruthy();
  });

  it("0 é valor válido: escala 0–10 tem 11 opções, 0 escolhível e legenda acima", () => {
    const onChange = vi.fn();
    const { container, getByRole, unmount } = render(
      <RatingScale
        {...baseProps({
          min: 0,
          max: 10,
          value: 0,
          onChange,
          endLabels: { min: "0 · Nada", max: "10 · Muito" },
          endLabelsPosition: "above",
          narrowColumns: 6,
        })}
      />,
    );
    const radios = container.querySelectorAll('input[type="radio"]');
    expect(radios).toHaveLength(11);
    expect(getByRole("radio", { name: "0 — significado 0" })).toBeTruthy();
    expect(
      container.querySelector<HTMLInputElement>('input[value="0"]')!.checked,
    ).toBe(true);

    // legenda acima: __ends vem antes de __options-row no DOM
    const scale = container.firstElementChild!;
    expect(scale.firstElementChild!.className).toContain(
      "delpi-ui-form-scale__ends",
    );
    expect(scale.textContent).toContain("0 · Nada");
    expect(scale.textContent).toContain("10 · Muito");

    const options = container.querySelector<HTMLElement>(
      ".delpi-ui-form-scale__options",
    )!;
    expect(
      options.style.getPropertyValue("--delpi-ui-form-scale-cols"),
    ).toBe("6");
    expect(options.className).toContain(
      "delpi-ui-form-scale__options--dense",
    );

    // 0 é escolhível: clicar na nota 0 (desmarcada) chama onChange(0)
    unmount();
    const onPick = vi.fn();
    const second = render(
      <RatingScale {...baseProps({ min: 0, max: 10, onChange: onPick })} />,
    );
    fireEvent.click(
      second.getByRole("radio", { name: "0 — significado 0" }),
    );
    expect(onPick).toHaveBeenCalledWith(0);
  });

  it("selectionCaption só aparece com nota (não com N/A nem sem valor)", () => {
    const props = baseProps({
      selectionCaption: (n) => `Sua nota: ${n}`,
      notApplicable: { label: "Não se aplica" },
    });
    const { container, rerender } = render(<RatingScale {...props} />);
    expect(
      container.querySelector(".delpi-ui-form-scale__caption"),
    ).toBeNull();

    rerender(<RatingScale {...props} value={4} />);
    expect(
      container.querySelector(".delpi-ui-form-scale__caption")!.textContent,
    ).toBe("Sua nota: 4");

    rerender(<RatingScale {...props} value="na" />);
    expect(
      container.querySelector(".delpi-ui-form-scale__caption"),
    ).toBeNull();
  });

  it("describedBy vai para o grupo; inválido aplica classe e aria-invalid", () => {
    const { container } = render(
      <RatingScale
        {...baseProps({
          invalid: true,
          describedBy: "erro-q1",
          notApplicable: { label: "Não se aplica" },
        })}
      />,
    );
    const group = container.querySelector('[role="group"]')!;
    expect(group.getAttribute("aria-describedby")).toBe("erro-q1");
    expect(group.className).toContain("delpi-ui-form-scale--invalid");

    for (const radio of container.querySelectorAll('input[type="radio"]')) {
      expect(radio.getAttribute("aria-invalid")).toBe("true");
    }
  });

  it("endLabelsPosition='below' coloca a legenda depois das opções", () => {
    const { container } = render(<RatingScale {...baseProps()} />);
    const scale = container.firstElementChild!;
    expect(scale.lastElementChild!.className).toContain(
      "delpi-ui-form-scale__ends",
    );
  });
});
