import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import {
  blockCssStyle,
  createShapeBlock,
  parseComunicadoConfig,
  serializeComunicadoConfig,
} from "./comunicadoHelpers";
import { CustomMessageScreen } from "./NativeScreens";

describe("comunicadoHelpers", () => {
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

  it("mapeia textAlign para justifyContent no bloco (herdado por h1/p)", () => {
    const block = {
      id: "1",
      type: "heading" as const,
      content: "Titulo",
      frame: { x: 0, y: 0, w: 50, h: 20 },
      style: { textAlign: "right" as const },
    };
    expect(blockCssStyle(block).justifyContent).toBe("flex-end");
    expect(blockCssStyle(block).textAlign).toBe("right");
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
