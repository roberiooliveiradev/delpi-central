import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ChartOverlayOptionsPopover,
  summarizeChartOverlayOptions,
} from "./ChartOverlayOptionsPopover";
import {
  buildCompareYearsOverlayOptions,
  clampCompareYears,
  compareYearOffsets,
} from "./compareYearsOverlay";

afterEach(() => cleanup());

describe("summarizeChartOverlayOptions", () => {
  it("junta overlays ativos", () => {
    expect(
      summarizeChartOverlayOptions([
        {
          id: "a",
          label: "Ano anterior",
          summaryLabel: "Ano ant.",
          checked: true,
          onChange: () => undefined,
        },
        {
          id: "b",
          label: "Tendência",
          checked: true,
          onChange: () => undefined,
        },
      ]),
    ).toBe("Ano ant. · Tendência");
  });

  it("usa empty quando nenhum ativo", () => {
    expect(
      summarizeChartOverlayOptions(
        [{ id: "a", label: "X", checked: false, onChange: () => undefined }],
        "Opções",
      ),
    ).toBe("Opções");
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
