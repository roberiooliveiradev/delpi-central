import { describe, expect, it } from "vitest";

import {
  applyDisplayFormatSpecToBlock,
  resolveCurrentDisplayFormatSpec,
  resolveDisplayFormatDescriptor,
  resolveDisplayFormatTarget,
} from "./displayFormatSelection";

describe("displayFormatSelection", () => {
  it("mapa seleção → slot: eixo X vs valores", () => {
    const chart = {
      id: "c1",
      type: "chart_view" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      chartOptions: { valueFormat: "auto" as const, categoryLabelFormat: "raw" as const },
    };
    expect(
      resolveDisplayFormatTarget({
        selected: chart,
        selectedChartPart: { kind: "axis", axis: "x" },
      }),
    ).toBe("chartCategory");
    expect(
      resolveDisplayFormatTarget({
        selected: chart,
        selectedChartPart: { kind: "axis", axis: "y" },
      }),
    ).toBe("chartValue");
    expect(resolveDisplayFormatTarget({ selected: chart })).toBe("chartValue");
  });

  it("leitura: spec ganha do enum; gravação escreve spec + espelho", () => {
    const chart = {
      id: "c1",
      type: "chart_view" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      chartOptions: {
        valueFormat: "auto" as const,
        categoryLabelFormat: "raw" as const,
        displayCategoryFormat: {
          category: "date" as const,
          presetId: "date-short",
          pattern: "dd/mm/yyyy",
        },
      },
    };
    expect(
      resolveCurrentDisplayFormatSpec({
        selected: chart,
        selectedChartPart: { kind: "axis", axis: "x" },
      }).presetId,
    ).toBe("date-short");

    const patch = applyDisplayFormatSpecToBlock(
      { selected: { ...chart, chartOptions: { categoryLabelFormat: "raw" } } },
      { category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" },
    );
    expect(patch).toMatchObject({
      chartOptions: {
        displayValueFormat: expect.objectContaining({ category: "date" }),
        valueFormat: "auto",
      },
    });

    const catPatch = applyDisplayFormatSpecToBlock(
      {
        selected: chart,
        selectedChartPart: { kind: "axis", axis: "x" },
      },
      { category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" },
    );
    expect(catPatch).toMatchObject({
      chartOptions: {
        displayCategoryFormat: expect.objectContaining({ presetId: "date-short" }),
        categoryLabelFormat: "day",
      },
    });
  });

  it("tabela: sem coluna grava global; com headerCell/cell grava só nas colunas", () => {
    const table = {
      id: "t1",
      type: "table_view" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      tableOptions: { valueFormat: "auto" as const },
      tableProjection: {
        columns: [
          { key: "op", label: "OP", visible: true },
          { key: "qty", label: "Qtd. pendente", visible: true },
        ],
      },
    };

    const globalPatch = applyDisplayFormatSpecToBlock(
      { selected: table },
      { category: "currency", presetId: "currency-brl", currency: "BRL", decimalPlaces: 2 },
    );
    expect(globalPatch).toMatchObject({
      tableOptions: {
        displayValueFormat: expect.objectContaining({ category: "currency" }),
        valueFormat: "currency",
      },
    });

    const columnPatch = applyDisplayFormatSpecToBlock(
      {
        selected: table,
        selectedTablePart: { kind: "headerCell", colIndex: 1 },
        selectedTableParts: [{ kind: "headerCell", colIndex: 1 }],
      },
      { category: "percent", presetId: "percent", decimalPlaces: 1 },
    );
    expect(columnPatch).toMatchObject({
      tableProjection: {
        columns: [
          { key: "op", visible: true },
          {
            key: "qty",
            displayFormat: expect.objectContaining({ category: "percent" }),
            valueFormat: "percent",
          },
        ],
      },
    });
    expect(columnPatch).not.toHaveProperty("tableOptions");

    const fromCell = applyDisplayFormatSpecToBlock(
      {
        selected: table,
        selectedTablePart: { kind: "cell", rowIndex: 0, colIndex: 1 },
        selectedTableParts: [{ kind: "cell", rowIndex: 0, colIndex: 1 }],
      },
      { category: "number", presetId: "number-0", decimalPlaces: 0 },
    );
    expect(fromCell).toMatchObject({
      tableProjection: {
        columns: [
          expect.objectContaining({ key: "op" }),
          expect.objectContaining({
            key: "qty",
            displayFormat: expect.objectContaining({ category: "number" }),
          }),
        ],
      },
    });

    const descriptor = resolveDisplayFormatDescriptor({
      selected: table,
      selectedTablePart: { kind: "headerCell", colIndex: 1 },
      selectedTableParts: [{ kind: "headerCell", colIndex: 1 }],
    });
    expect(descriptor?.target).toBe("tableColumn");
    expect(descriptor?.hint).toContain("Qtd. pendente");
  });

  it("duas colunas da mesma tabela podem ter formatos distintos", () => {
    const table = {
      id: "t1",
      type: "table_view" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      tableOptions: { valueFormat: "auto" as const },
      tableProjection: {
        columns: [
          {
            key: "a",
            visible: true,
            displayFormat: { category: "currency" as const, currency: "BRL", decimalPlaces: 2 },
          },
          {
            key: "b",
            visible: true,
            displayFormat: { category: "percent" as const, decimalPlaces: 1 },
          },
        ],
      },
    };
    expect(
      resolveCurrentDisplayFormatSpec({
        selected: table,
        selectedTableParts: [{ kind: "headerCell", colIndex: 0 }],
      }).category,
    ).toBe("currency");
    expect(
      resolveCurrentDisplayFormatSpec({
        selected: table,
        selectedTableParts: [{ kind: "headerCell", colIndex: 1 }],
      }).category,
    ).toBe("percent");
  });

  it("grade: dataRef.displayFormat prevalece; aplicação não vaza para outras células", () => {
    const canvas = {
      id: "g1",
      type: "canvas_table" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      rows: 2,
      cols: 2,
      cells: [
        [
          {
            kind: "number" as const,
            value: 10,
            dataRef: {
              field: "oee",
              format: "number" as const,
              displayFormat: { category: "percent" as const, decimalPlaces: 1 },
            },
          },
          { kind: "number" as const, value: 20, format: "decimal" as const },
        ],
        [
          { kind: "number" as const, value: 30 },
          { kind: "text" as const, text: "x" },
        ],
      ],
    };

    expect(
      resolveCurrentDisplayFormatSpec({
        selected: canvas,
        selectedCanvasTableCell: { blockId: "g1", row: 0, col: 0 },
      }).category,
    ).toBe("percent");

    const patch = applyDisplayFormatSpecToBlock(
      {
        selected: canvas,
        selectedCanvasTableCell: { blockId: "g1", row: 0, col: 0 },
      },
      { category: "currency", presetId: "currency-brl", currency: "BRL", decimalPlaces: 2 },
    );
    const cells = (patch as { cells: typeof canvas.cells }).cells;
    expect(cells[0][0].dataRef?.displayFormat?.category).toBe("currency");
    expect(cells[0][0].dataRef?.format).toBe("currency");
    expect(cells[0][1].value).toBe(20);
    expect(cells[0][1].dataRef).toBeUndefined();
    expect(cells[1][0].displayFormat).toBeUndefined();
  });

  it("texto: textProjection e dois dataRefs distintos; estático sem Número", () => {
    const text = {
      id: "tx1",
      type: "text" as const,
      frame: { x: 0, y: 0, w: 40, h: 20 },
      content: "A  B",
      textProjection: {
        field: "open_orders",
        format: "number" as const,
        displayFormat: { category: "number" as const, decimalPlaces: 0 },
      },
      contentRuns: [
        {
          text: "A",
          dataRef: {
            field: "a",
            displayFormat: { category: "currency" as const, currency: "BRL" },
            format: "currency" as const,
          },
        },
        { text: " " },
        {
          text: "B",
          dataRef: {
            field: "b",
            displayFormat: { category: "percent" as const, decimalPlaces: 1 },
            format: "percent" as const,
          },
        },
      ],
    };

    expect(resolveDisplayFormatTarget({ selected: text })).toBe("textProjection");
    expect(
      resolveCurrentDisplayFormatSpec({ selected: text }).category,
    ).toBe("number");

    expect(
      resolveDisplayFormatTarget({
        selected: { ...text, textProjection: undefined },
        textEditSelection: { blockId: "tx1", start: 0, end: 1 },
      }),
    ).toBe("textDataRef");
    expect(
      resolveCurrentDisplayFormatSpec({
        selected: { ...text, textProjection: undefined },
        textEditSelection: { blockId: "tx1", start: 0, end: 1 },
      }).category,
    ).toBe("currency");
    expect(
      resolveCurrentDisplayFormatSpec({
        selected: { ...text, textProjection: undefined },
        textEditSelection: { blockId: "tx1", start: 2, end: 3 },
      }).category,
    ).toBe("percent");

    const runPatch = applyDisplayFormatSpecToBlock(
      {
        selected: { ...text, textProjection: undefined },
        textEditSelection: { blockId: "tx1", start: 0, end: 1 },
      },
      { category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" },
    );
    expect(runPatch).toMatchObject({
      contentRuns: [
        {
          dataRef: expect.objectContaining({
            displayFormat: expect.objectContaining({ category: "date" }),
            format: "date",
          }),
        },
        { text: " " },
        {
          dataRef: expect.objectContaining({
            displayFormat: expect.objectContaining({ category: "percent" }),
          }),
        },
      ],
    });

    expect(
      resolveDisplayFormatTarget({
        selected: {
          id: "static",
          type: "text" as const,
          frame: { x: 0, y: 0, w: 10, h: 10 },
          content: "olá",
        },
      }),
    ).toBeNull();
  });
});
