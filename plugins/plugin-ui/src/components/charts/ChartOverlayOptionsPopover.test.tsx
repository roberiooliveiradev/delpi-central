import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartOverlayOptionsPopover } from "./ChartOverlayOptionsPopover";
import {
  buildCompareYearsOverlayOptions,
  clampCompareYears,
  compareYearOffsets,
} from "./compareYearsOverlay";

afterEach(() => cleanup());

describe("ChartOverlayOptionsPopover trigger", () => {
  it("mantém só Opções mesmo com overlays ativos", () => {
    render(
      <ChartOverlayOptionsPopover
        idPrefix="test-ov-summary"
        options={[
          {
            id: "yoy-1",
            label: "Comparar ano anterior",
            summaryLabel: "Ano anterior",
            checked: true,
            onChange: () => undefined,
          },
          {
            id: "yoy-2",
            label: "+2 anos",
            summaryLabel: "Até −2 anos",
            checked: true,
            onChange: () => undefined,
          },
        ]}
      />,
    );
    const trigger = screen.getByRole("button", { name: "Opções do gráfico" });
    expect(trigger.textContent).toContain("Opções");
    expect(trigger.textContent).not.toContain("Ano anterior");
    expect(trigger.textContent).not.toContain("Até −2 anos");
  });

  it("aceita summaryLabel estável sem listar o que está marcado", () => {
    render(
      <ChartOverlayOptionsPopover
        idPrefix="test-ov-custom"
        summaryLabel="Sobreposições"
        emptySummaryLabel="Nenhuma"
        options={[
          {
            id: "yoy",
            label: "Comparar ano anterior",
            checked: true,
            onChange: () => undefined,
          },
        ]}
      />,
    );
    const trigger = screen.getByRole("button", { name: "Opções do gráfico" });
    expect(trigger.textContent).toContain("Sobreposições");
    expect(trigger.textContent).not.toContain("Nenhuma");
    expect(trigger.textContent).not.toContain("Comparar ano anterior");
  });
});

describe("compareYearsOverlay", () => {
  it("clamp e offsets", () => {
    expect(clampCompareYears(9)).toBe(3);
    expect(compareYearOffsets(2)).toEqual([-1, -2]);
  });

  it("cascata −1 → −2 → −3", () => {
    const onChange = vi.fn();
    const options = buildCompareYearsOverlayOptions({
      compareYears: 1,
      onCompareYearsChange: onChange,
      labels: {
        priorYear: "Comparar ano anterior",
        plus2: "+2 anos",
        plus3: "+3 anos",
        priorYearSummary: "Ano anterior",
        plus2Summary: "Até −2 anos",
        plus3Summary: "Até −3 anos",
      },
    });
    expect(options[0]?.checked).toBe(true);
    expect(options[1]?.disabled).toBe(false);
    expect(options[2]?.disabled).toBe(true);
    options[1]?.onChange(true);
    expect(onChange).toHaveBeenCalledWith(2);
  });
});

describe("ChartOverlayOptionsPopover", () => {
  it("abre painel e dispara onChange", () => {
    const onTrend = vi.fn();
    render(
      <ChartOverlayOptionsPopover
        idPrefix="test-ov"
        options={[
          {
            id: "trend",
            label: "Linha de tendência",
            checked: false,
            onChange: onTrend,
          },
        ]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Opções do gráfico" }));
    expect(screen.getByText("Opções do gráfico", { selector: "p" })).toBeTruthy();
    const label = screen.getByText("Linha de tendência").closest("label");
    expect(label).toBeTruthy();
    fireEvent.click(label!);
    expect(onTrend).toHaveBeenCalledWith(true);
  });
});
