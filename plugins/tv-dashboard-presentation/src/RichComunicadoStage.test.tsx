import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { RichComunicadoMasterLogo } from "./RichComunicadoMasterLogo";
import { RichComunicadoStage } from "./RichComunicadoStage";

describe("RichComunicadoStage (canônico editor ≡ TV)", () => {
  it("renderiza logo master e bloco de texto", () => {
    render(
      <RichComunicadoStage
        data={{
          version: 4,
          background: { type: "color", value: "#ffffff" },
          master: {
            enabled: true,
            logo: { url: "https://example.com/logo.png", frame: { x: 2, y: 2, w: 12, h: 10 } },
          },
          blocks: [
            {
              id: "t1",
              type: "heading",
              content: "Qualidade",
              frame: { x: 10, y: 10, w: 40, h: 10 },
            } as never,
          ],
        }}
      />,
    );
    expect(document.querySelector(".tdp-comunicado__master-logo")).toBeTruthy();
    expect(screen.getByText("Qualidade")).toBeTruthy();
  });

  it("RichComunicadoMasterLogo não renderiza sem url", () => {
    const { container } = render(<RichComunicadoMasterLogo url={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("imagem de fundo preenche o palco via camada cover", () => {
    const { container } = render(
      <RichComunicadoStage
        data={{
          version: 4,
          background: {
            type: "image",
            url: "/apps/tv-dashboard-api/public/present/t/media/bg?x=1",
          },
          blocks: [],
        }}
      />,
    );
    const img = container.querySelector("img.delpi-ui-comunicado__background") as HTMLImageElement | null;
    expect(img).toBeTruthy();
    expect(img?.getAttribute("src")).toContain("media/bg");
    expect(img?.getAttribute("alt")).toBe("");
    expect(img?.style.objectFit).toBe("cover");
    expect(img?.style.width).toBe("100%");
    expect(img?.style.height).toBe("100%");
    const root = container.querySelector(".tdp-native-screen.tdp-comunicado") as HTMLElement | null;
    expect(root?.style.backgroundImage).toBe("");
  });

  it("RichComunicadoMasterLogo usa url() com aspas (query string segura)", () => {
    const { container } = render(
      <RichComunicadoMasterLogo url="/apps/tv-dashboard-api/public/present/t/media/a?x=1" />,
    );
    const node = container.firstElementChild as HTMLElement;
    expect(node.style.backgroundImage).toContain(
      'url("/apps/tv-dashboard-api/public/present/t/media/a?x=1")',
    );
  });
});
