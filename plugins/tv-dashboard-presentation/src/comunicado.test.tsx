import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { parseComunicadoConfig, serializeComunicadoConfig } from "./comunicadoHelpers";
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
});
