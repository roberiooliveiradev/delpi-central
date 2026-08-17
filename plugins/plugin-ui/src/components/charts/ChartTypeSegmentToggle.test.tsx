import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartTypeSegmentToggle } from "./ChartTypeSegmentToggle";

afterEach(() => cleanup());

describe("ChartTypeSegmentToggle", () => {
  it("abre catálogo com ícones e aplica seleção column→Colunas", () => {
    const onChange = vi.fn();
    render(
      <ChartTypeSegmentToggle
        family="time_multi_series"
        value="line"
        onChange={onChange}
        idPrefix="test-type"
      />,
    );

    const trigger = screen.getByRole("button", { name: "Tipo de gráfico" });
    expect(trigger.textContent).toMatch(/Linhas/);
    fireEvent.click(trigger);

    expect(screen.getByText("Tipo de gráfico", { selector: "h3" })).toBeTruthy();
    fireEvent.click(screen.getByTitle("Colunas"));
    expect(onChange).toHaveBeenCalledWith("column");
  });

  it("não renderiza com um único tipo", () => {
    const { container } = render(
      <ChartTypeSegmentToggle
        family="categorical"
        value="bar"
        onChange={() => undefined}
      />,
    );
    expect(container.firstChild).toBeNull();
  });
});
