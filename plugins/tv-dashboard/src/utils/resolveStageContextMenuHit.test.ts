import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { resolveStageContextMenuHit } from "./resolveStageContextMenuHit";

const componentsBase = join(dirname(fileURLToPath(import.meta.url)), "../components");

describe("resolveStageContextMenuHit", () => {
  it("menu de contexto cancela tap-deselect e aplica ícone por updateBlock", () => {
    const composerSrc = readFileSync(join(componentsBase, "ComunicadoComposer.tsx"), "utf8");
    const menuSrc = readFileSync(join(componentsBase, "ComunicadoStageContextMenu.tsx"), "utf8");
    expect(composerSrc).toMatch(/cancelPendingTapDeselect\(\)/);
    expect(composerSrc).toMatch(/handleStageContextMenu/);
    expect(menuSrc).toMatch(/pickerTargetBlockId/);
    expect(menuSrc).toMatch(/updateBlock\(targetId/);
    expect(menuSrc).toMatch(/resolveContextMenuIconPickerTargetId/);
  });

  it("botão direito não seleciona no pointerdown nem no contextmenu", () => {
    const composerSrc = readFileSync(join(componentsBase, "ComunicadoComposer.tsx"), "utf8");
    const menuSrc = readFileSync(join(componentsBase, "ComunicadoStageContextMenu.tsx"), "utf8");
    const dragSrc = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "beginBlockStageDrag.ts"),
      "utf8",
    );
    expect(composerSrc).toMatch(/event\.button !== 0/);
    expect(composerSrc).toMatch(/só abre opções/);
    expect(composerSrc).not.toMatch(/if \(!isBlockSelected\(hit\.blockId\)\) \{\s*selectBlock/);
    expect(dragSrc).toMatch(/event\.button !== 0/);
    expect(menuSrc).toMatch(/não força seleção no right-click/);
    expect(menuSrc).not.toMatch(/if \(missing\) selectBlocksByIds\(menuSelectedIds\)/);
  });

  it("botão direito não inicia move/resize/rotate nem resize de partes", () => {
    const interactionSrc = readFileSync(
      join(componentsBase, "useCanvasBlockInteraction.ts"),
      "utf8",
    );
    const blockViewSrc = readFileSync(
      join(componentsBase, "ComunicadoEditorBlockView.tsx"),
      "utf8",
    );
    // startDrag é o ponto canônico de move/resize/rotate/adjust/endpoint.
    expect(interactionSrc).toMatch(
      /const startDrag = useCallback\(\s*\([\s\S]*?if \(Number\.isFinite\(event\.button\) && event\.button !== 0\) return/,
    );
    // Resize de partes (chart/kpi/input) não passa por startDrag.
    const partResizeGuards = blockViewSrc.match(
      /onPartResizePointerDown = useCallback\([\s\S]*?if \(Number\.isFinite\(event\.button\) && event\.button !== 0\) return/g,
    );
    expect(partResizeGuards?.length).toBeGreaterThanOrEqual(3);
  });

  it("prioriza blockId explícito", () => {
    expect(
      resolveStageContextMenuHit({
        blockId: "icon-1",
        eventTarget: document.body,
      }),
    ).toEqual({ type: "block", blockId: "icon-1" });
  });

  it("resolve ancestral data-block-id (handles / SVG)", () => {
    const wrap = document.createElement("div");
    wrap.setAttribute("data-block-id", "icon-2");
    const svg = document.createElement("div");
    wrap.appendChild(svg);
    document.body.appendChild(wrap);
    expect(resolveStageContextMenuHit({ eventTarget: svg })).toEqual({
      type: "block",
      blockId: "icon-2",
    });
    wrap.remove();
  });

  it("fundo sem bloco → empty", () => {
    expect(resolveStageContextMenuHit({ eventTarget: document.body })).toEqual({
      type: "empty",
    });
  });
});
