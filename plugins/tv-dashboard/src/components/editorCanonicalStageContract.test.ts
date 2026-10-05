import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const composerSrc = readFileSync(join(here, "ComunicadoComposer.tsx"), "utf8");
const stageSrc = readFileSync(
  join(here, "../../../tv-dashboard-presentation/src/RichComunicadoStage.tsx"),
  "utf8",
);
const frameSrc = readFileSync(
  join(here, "../../../plugin-ui/src/components/preview/ComunicadoStageFrame.tsx"),
  "utf8",
);
const editorCss = readFileSync(join(here, "../index.css"), "utf8");

function ruleBody(css: string, selector: string): string {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = css.match(new RegExp(`(^|[\\s}])${escaped}\\s*\\{([\\s\\S]*?)\\}`, "m"));
  return match?.[2] ?? "";
}

/**
 * Contrato «um slide = um palco»: o editor NÃO pode montar uma segunda
 * árvore de stage. Fundo, logo master, moldura dual-class, ordenação e
 * visibilidade dos blocos vêm de `RichComunicadoStage`; o editor só
 * adiciona chrome de interação via os pontos de extensão do palco.
 *
 * Anti-padrão regressado: `MasterLogoOverlay`/`RichComunicadoBackground`
 * direto no composer + mapa de blocos paralelo ao `ComunicadoBlockView`
 * da TV (duas pinturas do mesmo slide → drift garantido).
 */
describe("editor canonical stage contract", () => {
  it("o composer monta RichComunicadoStage como palco único", () => {
    expect(composerSrc).toMatch(/<RichComunicadoStage\b/);
    expect(composerSrc).toMatch(/renderBlock=\{/);
    expect(composerSrc).toMatch(/stageContentWrapper=\{/);
  });

  it("sem pintura duplicada de stage no editor", () => {
    // Overlay de logo e camada de fundo eram owners paralelos — removidos.
    expect(composerSrc).not.toMatch(/MasterLogoOverlay/);
    expect(composerSrc).not.toMatch(/RichComunicadoMasterLogo/);
    expect(composerSrc).not.toMatch(/RichComunicadoBackground/);
    // Nenhum mapa de blocos fora dos pontos de extensão do palco:
    // o único `blocks.map` permitido é chrome de seleção, não paint.
    expect(composerSrc).not.toMatch(/blocks\.map\(\(block\)\s*=>\s*<ComunicadoEditorBlockView/);
  });

  it("stageContentWrapper preserva a ilha __stage-content + chrome de seleção", () => {
    expect(composerSrc).toMatch(/td-composer__stage-content/);
    expect(composerSrc).toMatch(/BlockSelectionChromeOverlay/);
    expect(composerSrc).toMatch(/GroupTransformLayer/);
  });

  it("mídia protegida entra via overrides autenticados do palco", () => {
    expect(composerSrc).toMatch(/backgroundImageUrl=\{/);
    expect(composerSrc).toMatch(/masterLogoUrl=\{/);
    expect(composerSrc).toMatch(/customFonts=\{resolvedCustomFonts\}/);
    // Ordem canônica do palco: fundo do slide antes do master.
    expect(composerSrc).toMatch(/config\.background\s*\?\?/);
  });

  it("canvas do editor espelha a tipografia base do .delpi-ui-comunicado", () => {
    const canvasBody = ruleBody(editorCss, ".dashboard-tv-dashboard .td-composer__canvas");
    expect(canvasBody).toMatch(/^\s*line-height:\s*1\.4\s*;/m);
    expect(canvasBody).toMatch(/^\s*font-size:\s*16px\s*;/m);
    expect(canvasBody).toMatch(/^\s*padding:\s*0\s*;/m);
    expect(canvasBody).toMatch(/^\s*display:\s*block\s*;/m);
  });

  it("o palco canônico expõe os pontos de extensão consumidos pelo editor", () => {
    for (const prop of [
      "renderBlock",
      "stageLeadingOverlay",
      "stageContentWrapper",
      "stageTrailingOverlay",
      "customFonts",
      "backgroundImageUrl",
      "masterLogoUrl",
      "rootRef",
      "rootProps",
      "style",
    ]) {
      expect(stageSrc).toMatch(new RegExp(`${prop}[?:]`));
    }
    // Defaults preservados: sem wrapper → conteúdo direto (comportamento TV).
    expect(stageSrc).toMatch(/stageContentWrapper \? stageContentWrapper\(stageContent\) : stageContent/);
  });

  it("a moldura compartilhada encaminha ref e atributos extras ao root", () => {
    expect(frameSrc).toMatch(/forwardRef/);
    expect(frameSrc).toMatch(/\{\.\.\.rest\}/);
    expect(frameSrc).toMatch(/data-\$\{string\}/);
  });
});
