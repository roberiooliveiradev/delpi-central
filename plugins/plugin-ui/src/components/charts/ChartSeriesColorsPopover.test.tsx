import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import type { ComponentProps } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartSeriesColorsPopover } from "./ChartSeriesColorsPopover";

afterEach(() => cleanup());

const SERIES = [
  {
    dataKey: "faturamento",
    name: "Faturamento · Bruto",
    fill: "#089bdb",
    visible: true,
    trendCapable: true,
    trendEnabled: false,
    trendColor: null,
    trendDash: "dashed" as const,
    trendWidth: 3,
  },
  {
    dataKey: "quantidade",
    name: "Quantidade fornecida",
    fill: "#ea580c",
    visible: true,
    trendCapable: true,
    trendEnabled: false,
    trendColor: null,
    trendDash: "dashed" as const,
    trendWidth: 3,
  },
  {
    dataKey: "faturamento_prior",
    name: "Ano ant.",
    fill: "#94a3b8",
    visible: true,
    trendCapable: true,
    trendEnabled: false,
    trendColor: null,
    trendDash: "dashed" as const,
    trendWidth: 3,
  },
  {
    dataKey: "faturamento_prior_2",
    name: "−2 anos",
    fill: "#64748b",
    visible: true,
    trendCapable: true,
    trendEnabled: false,
    trendColor: null,
    trendDash: "dashed" as const,
    trendWidth: 3,
  },
  {
    dataKey: "faturamento_prior_3",
    name: "−3 anos",
    fill: "#475569",
    visible: true,
    trendCapable: true,
    trendEnabled: false,
    trendColor: null,
    trendDash: "dashed" as const,
    trendWidth: 3,
  },
  {
    dataKey: "quantidade_prior",
    name: "Qtd ano ant.",
    fill: "#fb923c",
    visible: true,
    trendCapable: true,
    trendEnabled: false,
    trendColor: null,
    trendDash: "dashed" as const,
    trendWidth: 3,
  },
];

function openInspector() {
  fireEvent.click(screen.getByRole("button", { name: "Configurar séries" }));
}

function chooseSeries(label: string) {
  fireEvent.click(screen.getByRole("button", { name: "Série" }));
  fireEvent.click(screen.getByRole("button", { name: label }));
}

function renderInspector(
  extra?: Partial<ComponentProps<typeof ChartSeriesColorsPopover>>,
) {
  return render(
    <ChartSeriesColorsPopover
      idPrefix="test-series"
      series={SERIES}
      onChange={() => undefined}
      {...extra}
    />,
  );
}

describe("ChartSeriesColorsPopover", () => {
  it("usa FormSelectControl por dataKey e não HTMLSelectElement nativo", () => {
    const onChange = vi.fn();
    renderInspector({ onChange, onTrendChange: () => undefined });
    openInspector();
    expect(document.querySelector("select")).toBeNull();
    expect(document.querySelector(".delpi-ui-select")).toBeTruthy();
    chooseSeries("Quantidade fornecida");
    expect(screen.getByRole("dialog", { name: "Configurar séries" })).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Cor da série Quantidade fornecida" }),
    ).toBeTruthy();
  });

  it("oculta, reativa e não remove a série da lista", () => {
    const onVisibleChange = vi.fn();
    const hidden = SERIES.map((entry) =>
      entry.dataKey === "quantidade" ? { ...entry, visible: false } : entry,
    );
    const { rerender } = renderInspector({ onVisibleChange });
    openInspector();
    chooseSeries("Quantidade fornecida");
    fireEvent.click(screen.getByLabelText("Visível"));
    expect(onVisibleChange).toHaveBeenCalledWith("quantidade", false);

    rerender(
      <ChartSeriesColorsPopover
        idPrefix="test-series"
        series={hidden}
        onChange={() => undefined}
        onVisibleChange={onVisibleChange}
      />,
    );
    expect(screen.getByRole("dialog", { name: "Configurar séries" })).toBeTruthy();
    chooseSeries("Quantidade fornecida");
    fireEvent.click(screen.getByLabelText("Visível"));
    expect(onVisibleChange).toHaveBeenCalledWith("quantidade", true);
  });

  it("ativa tendência da série selecionada, inclusive comparativas", () => {
    const onTrendChange = vi.fn();
    renderInspector({ onTrendChange });
    openInspector();
    fireEvent.click(screen.getByLabelText("Ativar"));
    expect(onTrendChange).toHaveBeenCalledWith("faturamento", true);

    for (const label of ["Ano ant.", "−2 anos", "−3 anos", "Qtd ano ant."]) {
      onTrendChange.mockClear();
      chooseSeries(label);
      expect(screen.getByLabelText("Ativar")).toBeTruthy();
      fireEvent.click(screen.getByLabelText("Ativar"));
    }
    expect(onTrendChange).toHaveBeenCalledWith("quantidade_prior", true);
  });

  it("mostra Tipo Linear como valor read-only, não como select", () => {
    renderInspector({
      onTrendChange: () => undefined,
      onTrendStyleChange: () => undefined,
      series: SERIES.map((entry) =>
        entry.dataKey === "faturamento"
          ? { ...entry, trendEnabled: true }
          : entry,
      ),
    });
    openInspector();
    expect(screen.getByText("Linear")).toBeTruthy();
    expect(
      screen.getByText("Linear").className,
    ).toContain("delpi-ui-chart-series-colors__readonly");
    expect(document.querySelector("select")).toBeNull();
    expect(screen.queryByRole("button", { name: "Tipo" })).toBeNull();
  });

  it("Estilo e Espessura usam FormSelectControl e não fecham o inspector", () => {
    const onTrendStyleChange = vi.fn();
    renderInspector({
      onTrendChange: () => undefined,
      onTrendStyleChange,
      series: SERIES.map((entry) =>
        entry.dataKey === "faturamento"
          ? { ...entry, trendEnabled: true }
          : entry,
      ),
    });
    openInspector();
    fireEvent.click(screen.getByRole("button", { name: "Estilo" }));
    fireEvent.click(screen.getByRole("button", { name: "Contínuo" }));
    expect(onTrendStyleChange).toHaveBeenCalledWith("faturamento", {
      dash: "solid",
    });
    expect(screen.getByRole("dialog", { name: "Configurar séries" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Espessura" }));
    fireEvent.click(screen.getByRole("button", { name: "Grossa" }));
    expect(onTrendStyleChange).toHaveBeenCalledWith("faturamento", {
      width: 4,
    });
    expect(document.querySelector("select")).toBeNull();
  });

  it("tendência Automática herda a cor da série e persiste vazio, não auto", () => {
    const onTrendStyleChange = vi.fn();
    renderInspector({
      onTrendChange: () => undefined,
      onTrendStyleChange,
      series: SERIES.map((entry) =>
        entry.dataKey === "faturamento"
          ? { ...entry, trendEnabled: true, trendColor: null, fill: "#ea580c" }
          : entry,
      ),
    });
    openInspector();
    const trigger = screen.getByRole("button", {
      name: "Cor da tendência Faturamento · Bruto",
    });
    expect(trigger.textContent).toContain("Automática");
    const preview = trigger.querySelector(
      ".delpi-ui-color-picker-trigger__preview",
    ) as HTMLElement;
    expect(preview.className).not.toContain("preview--auto");
    expect(preview.style.background).toMatch(/ea580c|234,\s*88,\s*12/i);

    fireEvent.click(trigger);
    const picker = screen.getByRole("dialog", {
      name: "Cor da tendência Faturamento · Bruto",
      hidden: true,
    });
    expect(
      within(picker).getByRole("button", { name: "Automática" }).getAttribute("aria-pressed"),
    ).toBe("true");
    fireEvent.click(within(picker).getByRole("button", { name: "#c00000" }));
    expect(onTrendStyleChange).toHaveBeenCalledWith("faturamento", { color: "#c00000" });

    onTrendStyleChange.mockClear();
    fireEvent.click(within(picker).getByRole("button", { name: "Automática" }));
    expect(onTrendStyleChange).toHaveBeenCalledWith("faturamento", { color: "" });
  });

  it("Ponderar período parcial fica nas opções da tendência, não em COLOR_ONLY", () => {
    const onIncompleteBucketWeightChange = vi.fn();
    renderInspector({
      onTrendChange: () => undefined,
      onTrendStyleChange: () => undefined,
      incompleteBucketWeighted: false,
      onIncompleteBucketWeightChange,
      series: SERIES.map((entry) =>
        entry.dataKey === "faturamento"
          ? { ...entry, trendEnabled: true, trendApplyIncompleteBucket: true }
          : entry.dataKey === "faturamento_prior"
            ? { ...entry, trendEnabled: true, trendApplyIncompleteBucket: false }
            : { ...entry, trendApplyIncompleteBucket: false },
      ),
    });
    openInspector();
    fireEvent.click(screen.getByLabelText("Ponderar período parcial"));
    expect(onIncompleteBucketWeightChange).toHaveBeenCalledWith(true);

    chooseSeries("Ano ant.");
    const comparative = screen.getByLabelText(
      "Ponderar período parcial",
    ) as HTMLInputElement;
    expect(comparative.disabled).toBe(true);
  });

  it("com tendência desligada não mostra ponderar mesmo com callback", () => {
    renderInspector({
      onTrendChange: () => undefined,
      incompleteBucketWeighted: false,
      onIncompleteBucketWeightChange: () => undefined,
    });
    openInspector();
    expect(screen.queryByLabelText("Ponderar período parcial")).toBeNull();
  });

  it("sem callback de ponderação não mostra o checkbox", () => {
    renderInspector({
      onTrendChange: () => undefined,
      series: SERIES.map((entry) =>
        entry.dataKey === "faturamento" ? { ...entry, trendEnabled: true } : entry,
      ),
    });
    openInspector();
    expect(screen.queryByLabelText("Ponderar período parcial")).toBeNull();
  });

  it("COLOR_ONLY não exibe seção de tendência mesmo com série capable", () => {
    renderInspector();
    openInspector();
    expect(screen.queryByLabelText("Ativar")).toBeNull();
    expect(screen.queryByText("Linha de tendência")).toBeNull();
    expect(screen.queryByLabelText("Ponderar período parcial")).toBeNull();
  });

  it("série com opt-out de tendência não mostra Ativar", () => {
    renderInspector({
      onTrendChange: () => undefined,
      series: [
        {
          ...SERIES[0],
          trendCapable: false,
        },
      ],
    });
    openInspector();
    expect(screen.queryByLabelText("Ativar")).toBeNull();
  });

  it("altera a cor só da série selecionada, por dataKey", () => {
    const onChange = vi.fn();
    renderInspector({ onChange });
    openInspector();
    chooseSeries("Quantidade fornecida");
    fireEvent.click(
      screen.getByRole("button", { name: "Cor da série Quantidade fornecida" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "#c00000" }));
    expect(onChange).toHaveBeenCalledWith("quantidade", "#c00000");
    expect(onChange).not.toHaveBeenCalledWith("faturamento", expect.anything());
  });

  it("reset restaura a série selecionada", () => {
    const onResetSeries = vi.fn();
    renderInspector({ onResetSeries });
    openInspector();
    chooseSeries("Quantidade fornecida");
    fireEvent.click(screen.getByRole("button", { name: "Restaurar padrão" }));
    expect(onResetSeries).toHaveBeenCalledWith("quantidade");
  });

  it("separa seções com blocos e coloca Estilo e Espessura lado a lado", () => {
    renderInspector({
      onTrendChange: () => undefined,
      onTrendStyleChange: () => undefined,
      series: SERIES.map((entry) =>
        entry.dataKey === "faturamento"
          ? { ...entry, trendEnabled: true }
          : entry,
      ),
    });
    openInspector();
    expect(
      document.querySelectorAll(".delpi-ui-chart-series-colors__block").length,
    ).toBeGreaterThanOrEqual(3);
    expect(document.querySelector(".delpi-ui-chart-series-colors__pair")).toBeTruthy();
  });

  it("mostra ajuda nas seções quando o host passa hints", () => {
    renderInspector({
      onVisibleChange: () => undefined,
      onTrendChange: () => undefined,
      hints: {
        series: "Escolha qual série editar nesta lista.",
        appearance: "Cor e visibilidade só desta série.",
        trend: "Regressão linear só da série escolhida.",
      },
    });
    openInspector();
    fireEvent.mouseEnter(screen.getByText("Série"));
    expect(
      screen.getByRole("tooltip", { hidden: true }).textContent,
    ).toContain("série editar");
    expect(
      document.querySelectorAll(".delpi-ui-chart-series-colors__hint").length,
    ).toBeGreaterThan(1);
  });

  it("COLOR_ONLY não monta ajuda de tendência mesmo com hint", () => {
    renderInspector({
      hints: {
        series: "Escolha qual série editar nesta lista.",
        trend: "Não deve aparecer nesta superfície COLOR_ONLY.",
      },
    });
    openInspector();
    expect(screen.queryByText("Linha de tendência")).toBeNull();
    expect(
      screen.queryByText("Não deve aparecer nesta superfície COLOR_ONLY."),
    ).toBeNull();
  });
});
