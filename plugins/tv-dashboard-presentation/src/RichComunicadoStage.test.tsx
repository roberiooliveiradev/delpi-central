import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ComunicadoBlockView } from "./comunicadoBlockView";
import { RichComunicadoMasterLogo } from "./RichComunicadoMasterLogo";
import { RichComunicadoStage } from "./RichComunicadoStage";
import { resolveBlockPlacementStyle } from "./comunicadoShapeGeometry";

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

  it("com brandThemeKey Delpi claro → logo brand onLight", () => {
    const { container } = render(
      <RichComunicadoStage
        data={{
          version: 5,
          background: { type: "color", value: "#ffffff" },
          brandThemeKey: "delpi-light",
          blocks: [],
        }}
      />,
    );
    const logo = container.querySelector(".tdp-comunicado__master-logo") as HTMLImageElement | null;
    expect(logo).toBeTruthy();
    expect(logo?.tagName).toBe("IMG");
    expect(logo?.getAttribute("src") || "").toMatch(/logoDelpiOnLight|assets\//);
  });

  it("fundo escuro com brandThemeKey Delpi → logo brand onDark", () => {
    const { container } = render(
      <RichComunicadoStage
        data={{
          version: 5,
          background: { type: "color", value: "#0f172a" },
          brandThemeKey: "delpi-dark",
          blocks: [],
        }}
      />,
    );
    const logo = container.querySelector(".tdp-comunicado__master-logo") as HTMLImageElement | null;
    expect(logo).toBeTruthy();
    expect(logo?.getAttribute("src") || "").toMatch(/logoDelpiOnDark|assets\//);
  });

  it("negativo: sem brandThemeKey → sem logo automática", () => {
    const { container } = render(
      <RichComunicadoStage
        data={{
          version: 5,
          background: { type: "color", value: "#0f172a" },
          blocks: [],
        }}
      />,
    );
    expect(container.querySelector(".tdp-comunicado__master-logo")).toBeNull();
  });

  describe("pontos de extensão do editor", () => {
    const stageData = {
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
    };

    it("renderBlock substitui o mapa padrão mantendo ordem dentro do __stage", () => {
      const { container } = render(
        <RichComunicadoStage
          data={stageData}
          renderBlock={(block) => (
            <div className="editor-wrap" data-block-id={block.id}>
              bloco {block.id}
            </div>
          )}
        />,
      );
      const stage = container.querySelector(".tdp-comunicado__stage");
      const wrap = stage?.querySelector(".editor-wrap");
      expect(wrap).toBeTruthy();
      expect(wrap?.getAttribute("data-block-id")).toBe("t1");
      expect(stage?.querySelector(".tdp-comunicado__block")).toBeNull();
      // Logo continua no owner canônico mesmo com renderer customizado.
      expect(stage?.querySelector(".tdp-comunicado__master-logo")).toBeTruthy();
    });

    it("stageLeadingOverlay/stageTrailingOverlay entram como irmãos dentro do __stage", () => {
      const { container } = render(
        <RichComunicadoStage
          data={stageData}
          stageLeadingOverlay={<div className="lead" />}
          stageTrailingOverlay={<div className="trail" />}
        />,
      );
      const stage = container.querySelector(".tdp-comunicado__stage");
      expect(stage?.firstElementChild?.className).toBe("lead");
      expect(stage?.lastElementChild?.className).toBe("trail");
    });

    it("stageContentWrapper isola logo+blocos em ilha de conteúdo", () => {
      const { container } = render(
        <RichComunicadoStage
          data={stageData}
          stageContentWrapper={(content) => <div className="content-island">{content}</div>}
        />,
      );
      const island = container.querySelector(".tdp-comunicado__stage > .content-island");
      expect(island).toBeTruthy();
      expect(island?.querySelector(".tdp-comunicado__master-logo")).toBeTruthy();
      expect(island?.textContent).toContain("Qualidade");
    });

    it("overrides de imagem: null suprime camada; URL substitui resolução do data", () => {
      const { container, rerender } = render(
        <RichComunicadoStage
          data={stageData}
          masterLogoUrl={null}
          backgroundImageUrl={null}
        />,
      );
      expect(container.querySelector(".tdp-comunicado__master-logo")).toBeNull();
      rerender(
        <RichComunicadoStage
          data={stageData}
          masterLogoUrl="blob:logo-resolvido"
        />,
      );
      const logo = container.querySelector(
        ".tdp-comunicado__master-logo",
      ) as HTMLImageElement | null;
      expect(logo?.getAttribute("src")).toBe("blob:logo-resolvido");
    });

    it("style/rootRef/rootProps pousam no root da moldura", () => {
      const rootRef = { current: null as HTMLDivElement | null };
      const onContextMenu = () => undefined;
      const { container } = render(
        <RichComunicadoStage
          data={stageData}
          style={{ width: 1920, transform: "scale(0.54)" }}
          rootRef={rootRef}
          rootProps={{ "data-viewport": "1080p", onContextMenu }}
        />,
      );
      const root = container.querySelector(".tdp-comunicado") as HTMLElement | null;
      expect(root).toBeTruthy();
      expect(root?.style.transform).toBe("scale(0.54)");
      expect(root?.getAttribute("data-viewport")).toBe("1080p");
      expect(rootRef.current).toBe(root);
    });
  });

  describe("paridade editor ≡ TV — fixture FATURAMENTO ANO", () => {
    /*
     * Espelha a estrutura do slide do incidente: título + período,
     * rótulos de seção, cards, separadores verticais (shape line),
     * linha TOTAL e logo master. O editor monta o MESMO componente
     * com renderBlock/overlays — o paint canônico não pode divergir.
     */
    const faturamentoSlide = {
      version: 4,
      background: { type: "color", value: "#0b1220" },
      brandThemeKey: "delpi-dark",
      blocks: [
        { id: "title", type: "heading", content: "FATURAMENTO ANO",
          frame: { x: 4, y: 3, w: 50, h: 8 }, style: { zIndex: 1 } } as never,
        { id: "period", type: "text", content: "JAN – DEZ 2025",
          frame: { x: 4, y: 12, w: 40, h: 5 }, style: { zIndex: 1 } } as never,
        { id: "sec-ano", type: "text", content: "ANO",
          frame: { x: 6, y: 24, w: 28, h: 6 }, style: { zIndex: 1 } } as never,
        { id: "sec-mes", type: "text", content: "MÊS",
          frame: { x: 38, y: 24, w: 28, h: 6 }, style: { zIndex: 1 } } as never,
        { id: "sec-carteira", type: "text", content: "CARTEIRA",
          frame: { x: 70, y: 24, w: 26, h: 6 }, style: { zIndex: 1 } } as never,
        { id: "card-sc", type: "shape", shape: "rectangle", content: "",
          frame: { x: 6, y: 34, w: 26, h: 40 }, style: { zIndex: 0 } } as never,
        { id: "card-es", type: "shape", shape: "rectangle", content: "",
          frame: { x: 6, y: 54, w: 26, h: 20 }, style: { zIndex: 0 } } as never,
        { id: "sep-1", type: "shape", shape: "line", content: "",
          frame: { x: 35, y: 30, w: 0.5, h: 55 }, style: { zIndex: 2 } } as never,
        { id: "sep-2", type: "shape", shape: "line", content: "",
          frame: { x: 67, y: 30, w: 0.5, h: 55 }, style: { zIndex: 2 } } as never,
        { id: "total", type: "text", content: "TOTAL",
          frame: { x: 6, y: 82, w: 88, h: 8 }, style: { zIndex: 1 } } as never,
      ],
    };

    /**
     * Extrai paint canônico: logo + por-bloco {classes, left/top/w/h, zIndex}.
     * Em modo editor o posicionamento vive no wrap de interação (o bloco
     * canônico é `embedded`) — mede-se o elemento que carrega o frame.
     */
    function canonicalPaint(container: HTMLElement, viaWrap = false) {
      const logo = container.querySelector(".tdp-comunicado__master-logo") as HTMLElement | null;
      const blocks = Array.from(
        container.querySelectorAll<HTMLElement>(".tdp-comunicado__block"),
      ).map((el) => {
        const posEl = viaWrap
          ? ((el.closest(".td-composer__block-wrap") as HTMLElement | null) ?? el)
          : el;
        return {
          classes: el.className,
          left: posEl.style.left,
          top: posEl.style.top,
          width: posEl.style.width,
          height: posEl.style.height,
          zIndex: posEl.style.zIndex,
        };
      });
      return {
        logo: logo
          ? {
              // Classes `td-composer__*` são chrome do editor — fora do contrato.
              classes: logo.className.replace(/td-composer__\S+/g, "").trim(),
              left: logo.style.left,
              top: logo.style.top,
              width: logo.style.width,
              height: logo.style.height,
              opacity: logo.style.opacity,
            }
          : null,
        blocks,
      };
    }

    it("mesmo slide → mesmos frames/logo/paint em modo apresentação e modo editor", () => {
      const { container: tv } = render(<RichComunicadoStage data={faturamentoSlide} />);
      const { container: editor } = render(
        <RichComunicadoStage
          data={faturamentoSlide}
          className="td-composer__canvas delpi-ui-comunicado delpi-ui-comunicado--editor tdp-comunicado"
          stageClassName="td-composer__stage tdp-comunicado__stage"
          masterLogoClassName="td-composer__master-logo tdp-comunicado__master-logo"
          style={{ width: 1920, height: 1080, transform: "scale(0.54)", transformOrigin: "top left" }}
          renderBlock={(block) => (
            <div
              className="td-composer__block-wrap"
              data-block-id={block.id}
              style={{
                position: "absolute",
                ...resolveBlockPlacementStyle(block),
                zIndex: block.style?.zIndex ?? 1,
              }}
            >
              <ComunicadoBlockView block={block} fontScale={1} embedded />
            </div>
          )}
          stageContentWrapper={(content) => (
            <div className="td-composer__stage-content">{content}</div>
          )}
          stageLeadingOverlay={<div className="td-composer__stage-grid" />}
          stageTrailingOverlay={<div className="td-composer__stage-guide" />}
        />,
      );

      const tvPaint = canonicalPaint(tv);
      const editorPaint = canonicalPaint(editor, true);

      // Mesma contagem e ordem de blocos (título, período, seções, cards, seps, total).
      expect(editorPaint.blocks.length).toBe(tvPaint.blocks.length);
      expect(editorPaint.blocks.length).toBe(10);
      expect(editorPaint.blocks.map((b) => b.classes)).toEqual(
        tvPaint.blocks.map((b) => b.classes),
      );

      // Geometria normalizada idêntica (design px → % do palco, mesma origem).
      for (let i = 0; i < tvPaint.blocks.length; i += 1) {
        expect(editorPaint.blocks[i].left).toBe(tvPaint.blocks[i].left);
        expect(editorPaint.blocks[i].top).toBe(tvPaint.blocks[i].top);
        expect(editorPaint.blocks[i].width).toBe(tvPaint.blocks[i].width);
        expect(editorPaint.blocks[i].height).toBe(tvPaint.blocks[i].height);
        expect(editorPaint.blocks[i].zIndex).toBe(tvPaint.blocks[i].zIndex);
      }

      // Logo: mesma moldura/opacidade (resolvida pelo mesmo owner canônico).
      expect(editorPaint.logo).toEqual(tvPaint.logo);

      // Overlays do editor existem, mas não perturbam o conteúdo canônico.
      const editorStage = editor.querySelector(".td-composer__stage");
      expect(editorStage?.querySelector(".td-composer__stage-grid")).toBeTruthy();
      expect(editorStage?.querySelector(".td-composer__stage-guide")).toBeTruthy();
      expect(
        editorStage?.querySelectorAll(".td-composer__block-wrap").length,
      ).toBe(10);
    });

    it("zoom do editor não altera métricas de design (outer scale ≠ design layout)", () => {
      const zooms = [0.54, 1, 1.35];
      const paints = zooms.map((zoom) => {
        const { container } = render(
          <RichComunicadoStage
            data={faturamentoSlide}
            style={{
              width: 1920,
              height: 1080,
              transform: `scale(${zoom})`,
              transformOrigin: "top left",
            }}
          />,
        );
        const paint = canonicalPaint(container);
        return JSON.stringify(paint);
      });
      expect(paints[0]).toBe(paints[1]);
      expect(paints[1]).toBe(paints[2]);
    });
  });
});
