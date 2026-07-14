import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InspectorElementRow } from "./InspectorElementRow";

afterEach(() => {
  cleanup();
});

describe("InspectorElementRow", () => {
  it("usa label-btn (não botão de tema) e checkbox quando habilitável", () => {
    const onToggle = vi.fn();
    const onSelect = vi.fn();
    const { container } = render(
      <InspectorElementRow
        id="td-test-el"
        label="Linha de cabeçalho"
        enabled
        onToggle={onToggle}
        onSelect={onSelect}
      />,
    );
    const labelBtn = container.querySelector(".td-chart-element__label-btn");
    expect(labelBtn).toBeTruthy();
    expect(container.querySelector(".td-chart-element__label:not(.td-chart-element__label-btn)")).toBeNull();
    fireEvent.click(labelBtn!);
    expect(onSelect).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("checkbox", { name: /Exibir Linha de cabeçalho/i }));
    expect(onToggle).toHaveBeenCalledWith(false);
  });

  it("mantém coluna de toggle com spacer quando só seleciona", () => {
    const { container } = render(
      <InspectorElementRow id="td-frame" label="Moldura" onSelect={() => undefined} />,
    );
    expect(container.querySelector(".td-chart-element__toggle-spacer")).toBeTruthy();
    expect(container.querySelector('input[type="checkbox"]')).toBeNull();
  });

  it("respeita toggleDisabled no checkbox", () => {
    render(
      <InspectorElementRow
        id="td-control"
        label="Controle"
        enabled
        toggleDisabled
        onToggle={() => undefined}
        onSelect={() => undefined}
      />,
    );
    expect(
      (screen.getByRole("checkbox", { name: /Exibir Controle/i }) as HTMLInputElement).disabled,
    ).toBe(true);
  });
});
