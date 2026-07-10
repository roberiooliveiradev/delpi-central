import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import {
  blockTypeForDisplayMode,
  listDataPresentationOptions,
} from "./comunicadoDataPresentation";
import {
  blockCssStyle,
  buildTextDecoration,
  clampFontSize,
  comunicadoTextInnerStyle,
  createShapeBlock,
  parseComunicadoConfig,
  parseTextDecorationFlags,
  serializeComunicadoConfig,
} from "./comunicadoHelpers";
import { CustomMessageScreen } from "./NativeScreens";

describe("comunicadoHelpers", () => {
  it("mantém slide vazio quando blocks é array vazio", () => {
    const parsed = parseComunicadoConfig({
      version: 2,
      blocks: [],
      background: { type: "color", value: "#ffffff" },
    });
    expect(parsed.blocks).toEqual([]);
    expect(parsed.background).toEqual({ type: "color", value: "#ffffff" });
  });

  it("round-trip de slide vazio não reintroduz blocos padrão", () => {
    const empty = parseComunicadoConfig({
      version: 2,
      blocks: [],
      background: { type: "color", value: "#ffffff" },
    });
    const serialized = serializeComunicadoConfig(empty);
    const roundtrip = parseComunicadoConfig(serialized);
    expect(roundtrip.blocks).toEqual([]);
  });

  it("mescla estilo padrão quando bloco vem com style vazio", () => {
    const parsed = parseComunicadoConfig({
      version: 2,
      blocks: [
        {
          id: "h1",
          type: "heading",
          content: "Título",
          frame: { x: 5, y: 12, w: 90, h: 18 },
          style: {},
        },
      ],
    });
    const heading = parsed.blocks?.[0];
    expect(heading?.type).toBe("heading");
    if (heading?.type === "heading") {
      expect(heading.style?.fontSize).toBe(56);
    }
  });

  it("converte legado headline/subtitle em blocos", () => {
    const parsed = parseComunicadoConfig({ headline: "Aviso", subtitle: "Detalhe" });
    expect(parsed.blocks?.length).toBe(2);
    expect(parsed.blocks?.[0]?.type).toBe("heading");
  });

  it("serializa blocos mantendo headline", () => {
    const parsed = parseComunicadoConfig({ headline: "Titulo" });
    const serialized = serializeComunicadoConfig(parsed);
    expect(serialized.version).toBe(2);
    expect(serialized.headline).toBe("Titulo");
  });

  it("persiste animações de entrada por bloco", () => {
    const parsed = parseComunicadoConfig({
      version: 3,
      blocks: [
        {
          id: "1",
          type: "text",
          content: "Entrada",
          frame: { x: 0, y: 0, w: 40, h: 20 },
          animations: [{ phase: "entrance", kind: "fade", delayMs: 150, durationMs: 700 }],
        },
      ],
    });
    const serialized = serializeComunicadoConfig(parsed);
    const blocks = serialized.blocks as Array<Record<string, unknown>>;
    expect(blocks[0].animations).toEqual([
      { phase: "entrance", kind: "fade", delayMs: 150, durationMs: 700 },
    ]);
    const roundtrip = parseComunicadoConfig(serialized);
    expect(roundtrip.blocks?.[0]?.animations?.[0]?.kind).toBe("fade");
  });

  it("serializa v3 com formas e links", () => {
    const shape = createShapeBlock("rectangle");
    const parsed = parseComunicadoConfig({
      version: 3,
      blocks: [
        {
          id: "1",
          type: "text",
          content: "Saiba mais",
          href: "https://example.com",
          frame: { x: 10, y: 10, w: 40, h: 20 },
          style: { fontFamily: "Arial, sans-serif" },
        },
        shape,
      ],
    });
    const serialized = serializeComunicadoConfig(parsed);
    expect(serialized.version).toBe(3);
    const blocks = serialized.blocks as Array<Record<string, unknown>>;
    expect(blocks[0].href).toBe("https://example.com");
    expect(blocks[1].type).toBe("shape");
  });

  it("mapeia verticalAlign para justifyContent no bloco flex", () => {
    const block = {
      id: "1",
      type: "heading" as const,
      content: "Titulo",
      frame: { x: 0, y: 0, w: 50, h: 20 },
      style: { verticalAlign: "bottom" as const, textAlign: "right" as const },
    };
    expect(blockCssStyle(block).justifyContent).toBe("flex-end");
    expect(blockCssStyle(block).textAlign).toBe("right");
  });

  it("aplica estilo interno de texto com realce e tachado", () => {
    const block = {
      id: "1",
      type: "text" as const,
      content: "Corpo",
      frame: { x: 0, y: 0, w: 50, h: 20 },
      style: {
        textHighlight: "#fef08a",
        letterSpacing: 2,
        textDecoration: buildTextDecoration(true, true),
      },
    };
    const inner = comunicadoTextInnerStyle(block);
    expect(inner.backgroundColor).toBe("#fef08a");
    expect(inner.letterSpacing).toBe("2px");
    expect(inner.textDecoration).toBe("underline line-through");
    expect(parseTextDecorationFlags("underline line-through")).toEqual({
      underline: true,
      strikethrough: true,
    });
  });

  it("limita tamanho da fonte", () => {
    expect(clampFontSize(8)).toBe(12);
    expect(clampFontSize(200)).toBe(120);
  });

  it("serializa blocos data_* e dataFilters (v4)", () => {
    const parsed = parseComunicadoConfig({
      version: 4,
      dataFilters: { branch: "01", periodDays: 30 },
      blocks: [
        {
          id: "kpi-1",
          type: "data_kpi",
          frame: { x: 5, y: 28, w: 28, h: 22 },
          dataBinding: {
            operationId: "get_overall_equipment_effectiveness_pct",
            params: { periodDays: 7 },
            displayMode: "kpi",
            label: "OEE",
          },
        },
      ],
    });
    expect(parsed.version).toBe(4);
    expect(parsed.dataFilters?.branch).toBe("01");
    const serialized = serializeComunicadoConfig(parsed);
    expect(serialized.version).toBe(4);
    expect(serialized.dataFilters).toEqual({ branch: "01", periodDays: 30 });
    const blocks = serialized.blocks as Array<Record<string, unknown>>;
    expect(blocks[0].type).toBe("data_kpi");
    expect((blocks[0].dataBinding as Record<string, unknown>).operationId).toBe(
      "get_overall_equipment_effectiveness_pct",
    );
    expect(blocks[0].resolved).toBeUndefined();
  });

  it("serializa fundo gradiente", () => {
    const serialized = serializeComunicadoConfig({
      version: 3,
      background: { type: "gradient", from: "#111827", to: "#089bdb", angle: 135 },
      blocks: [],
    });
    expect(serialized.background).toEqual({
      type: "gradient",
      from: "#111827",
      to: "#089bdb",
      angle: 135,
    });
  });

  it("normaliza contentRuns e mantém content legado", () => {
    const parsed = parseComunicadoConfig({
      blocks: [
        {
          id: "1",
          type: "text",
          content: "legado",
          frame: { x: 0, y: 0, w: 50, h: 20 },
        },
        {
          id: "2",
          type: "heading",
          content: "Titulo",
          contentRuns: [
            { text: "Tit", style: { fontWeight: "bold" } },
            { text: "ulo", style: { fontStyle: "italic" } },
          ],
          frame: { x: 0, y: 0, w: 50, h: 20 },
        },
      ],
    });
    const legacy = parsed.blocks?.find((block) => block.id === "1");
    expect(legacy && "content" in legacy ? legacy.content : "").toBe("legado");
    expect(legacy && "contentRuns" in legacy ? legacy.contentRuns : undefined).toBeUndefined();

    const rich = parsed.blocks?.find((block) => block.id === "2");
    expect(rich && "content" in rich ? rich.content : "").toBe("Titulo");
    expect(rich && "contentRuns" in rich ? rich.contentRuns?.length : 0).toBe(2);

    const serialized = serializeComunicadoConfig(parsed);
    const blocks = serialized.blocks as Array<Record<string, unknown>>;
    expect(blocks[0].contentRuns).toBeUndefined();
    expect(blocks[0].content).toBe("legado");
    expect(blocks[1].contentRuns).toEqual([
      { text: "Tit", style: { fontWeight: "bold" } },
      { text: "ulo", style: { fontStyle: "italic" } },
    ]);
    expect(blocks[1].content).toBe("Titulo");

    const roundTrip = parseComunicadoConfig(serialized);
    const roundRich = roundTrip.blocks?.find((block) => block.id === "2");
    expect(roundRich && "content" in roundRich ? roundRich.content : "").toBe("Titulo");
  });

  it("não persiste URL de mídia no native_config", () => {
    const parsed = parseComunicadoConfig({
      blocks: [
        {
          id: "1",
          type: "image",
          assetId: "asset-1",
          url: "https://example.com/x.jpg",
          frame: { x: 0, y: 0, w: 50, h: 50 },
        },
      ],
      background: { type: "image", assetId: "bg-1", url: "https://example.com/bg.jpg" },
    });
    const serialized = serializeComunicadoConfig(parsed);
    const block = (serialized.blocks as Array<Record<string, unknown>>)[0];
    expect(block.url).toBeUndefined();
    expect(block.assetId).toBe("asset-1");
    expect(serialized.background).toEqual({ type: "image", assetId: "bg-1" });
  });
});

describe("comunicadoDataPresentation", () => {
  it("lista todos os formatos universais independente da rota", () => {
    const options = listDataPresentationOptions(["kpi", "auto"]);
    expect(options).toHaveLength(4);
    expect(options.map((option) => option.displayMode)).toEqual(
      expect.arrayContaining(["kpi", "table", "line_chart", "bar_chart"]),
    );
    expect(options.some((option) => option.displayMode === "auto")).toBe(false);
  });

  it("marca modos sugeridos como recomendados", () => {
    const options = listDataPresentationOptions(["line_chart"]);
    const line = options.find((option) => option.displayMode === "line_chart");
    expect(line?.recommended).toBe(true);
    const table = options.find((option) => option.displayMode === "table");
    expect(table?.recommended).toBe(false);
  });

  it("mapeia auto para data_kpi e table para data_table", () => {
    expect(blockTypeForDisplayMode("auto")).toBe("data_kpi");
    expect(blockTypeForDisplayMode("table")).toBe("data_table");
    expect(blockTypeForDisplayMode("bar_chart")).toBe("data_chart");
  });
});

describe("CustomMessageScreen rich layout", () => {
  it("renderiza blocos posicionados", () => {
    render(
      <CustomMessageScreen
        data={{
          version: 2,
          blocks: [
            {
              id: "1",
              type: "heading",
              content: "Campanha interna",
              frame: { x: 5, y: 10, w: 90, h: 20 },
              style: { fontSize: 48, color: "#fff", textAlign: "center" },
            },
          ],
          background: { type: "color", value: "#111827" },
        }}
      />,
    );
    expect(screen.getByText("Campanha interna")).toBeTruthy();
  });

  it("renderiza contentRuns com estilos parciais", () => {
    render(
      <CustomMessageScreen
        data={{
          version: 3,
          blocks: [
            {
              id: "1",
              type: "text",
              content: "ABC",
              contentRuns: [
                { text: "A", style: { fontWeight: "bold" } },
                { text: "BC", style: { fontStyle: "italic" } },
              ],
              frame: { x: 5, y: 10, w: 90, h: 20 },
              style: { fontSize: 24, color: "#fff", textAlign: "center" },
            },
          ],
          background: { type: "color", value: "#111827" },
        }}
      />,
    );
    expect(screen.getByText("A")).toBeTruthy();
    expect(screen.getByText("BC")).toBeTruthy();
  });

  it("renderiza lista com três itens e marcadores na TV", () => {
    const { container } = render(
      <CustomMessageScreen
        data={{
          version: 3,
          blocks: [
            {
              id: "1",
              type: "text",
              content: "Alpha\nBeta\nGamma",
              contentRuns: [
                { text: "Alpha", style: { listType: "bullet" } },
                { text: "\n" },
                { text: "Beta", style: { listType: "bullet" } },
                { text: "\n" },
                { text: "Gamma", style: { listType: "bullet" } },
              ],
              frame: { x: 5, y: 10, w: 90, h: 20 },
              style: { fontSize: 24, color: "#fff", textAlign: "left" },
            },
          ],
          background: { type: "color", value: "#111827" },
        }}
      />,
    );
    const list = container.querySelector(".tdp-comunicado__list--bullet");
    expect(list).toBeTruthy();
    expect(list?.querySelectorAll(".tdp-comunicado__list-item").length).toBe(3);
    expect(screen.getByText("Alpha")).toBeTruthy();
    expect(screen.getByText("Beta")).toBeTruthy();
    expect(screen.getByText("Gamma")).toBeTruthy();
  });

  it("renderiza forma e link", () => {
    render(
      <CustomMessageScreen
        data={{
          version: 3,
          blocks: [
            {
              id: "1",
              type: "shape",
              shape: "rectangle",
              content: "Destaque",
              frame: { x: 20, y: 20, w: 60, h: 30 },
              style: { fill: "#089bdb", stroke: "#fff", strokeWidth: 2, zIndex: 1 },
            },
            {
              id: "2",
              type: "text",
              content: "Clique aqui",
              href: "https://delpi.example",
              frame: { x: 10, y: 60, w: 80, h: 20 },
              style: { fontSize: 24, color: "#fff", textAlign: "center", zIndex: 2 },
            },
          ],
          background: { type: "color", value: "#111827" },
        }}
      />,
    );
    expect(screen.getByText("Destaque")).toBeTruthy();
    const link = screen.getByRole("link", { name: "Clique aqui" });
    expect(link.getAttribute("href")).toBe("https://delpi.example");
  });
});
