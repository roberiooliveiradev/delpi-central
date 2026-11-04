import { describe, expect, it } from "vitest";
import {
  applyComunicadoBlockStylePatch,
} from "./applyComunicadoBlockStylePatch";
import { fillToColorStylePatch } from "./delpiFillAdapter";
import {
  containerTypographyKeysFromRunPatch,
  reconcileDraftContentRunsForCommit,
} from "./reconcileDraftContentRuns";
import { sparsePropertyPatch } from "./selectionPropertyApply";

/**
 * Baseline A→B da família TV-EDITOR-STALE-DRAFT-MUTATION-RECONCILIATION.
 * Usa os produtores reais (style patch + draft flush), não um merge inventado.
 */
describe("reconcileDraftContentRunsForCommit", () => {
  const whiteRuns = [
    { text: "PPM INTERNO", style: { color: "#ffffff" as const } },
  ];

  function shapeBlock(runs = whiteRuns) {
    return {
      id: "b1",
      type: "shape" as const,
      shape: "rectangle" as const,
      content: "PPM INTERNO",
      contentRuns: runs,
      frame: { x: 0, y: 0, w: 20, h: 10 },
      style: { color: "#ffffff", fontSize: 28, zIndex: 2 },
    };
  }

  it("baseline A→B: flush com draftRef stale reintroduz branco sem reconciliação", () => {
    const initial = shapeBlock();
    const colorPatch = sparsePropertyPatch(
      fillToColorStylePatch({ kind: "solid", color: "#000000" }),
    );
    const afterA = applyComunicadoBlockStylePatch(initial, colorPatch);
    expect(afterA.style?.color).toBe("#000000");
    expect(afterA.type).toBe("shape");
    if (afterA.type !== "shape") return;
    expect(afterA.contentRuns?.every((run) => run.style?.color == null)).toBe(true);

    // Mutation B sem reconciliação: draft iniciado com branco.
    const flushedWithoutReconcile = {
      ...afterA,
      content: "PPM INTERNO",
      contentRuns: whiteRuns,
    };
    expect(flushedWithoutReconcile.contentRuns?.[0]?.style?.color).toBe("#ffffff");
    expect(flushedWithoutReconcile.style?.color).toBe("#000000");
  });

  it("após reconciliação o flush não reintroduz color stale do draft", () => {
    const initial = shapeBlock();
    const colorPatch = sparsePropertyPatch(
      fillToColorStylePatch({ kind: "solid", color: "#000000" }),
    );
    const afterA = applyComunicadoBlockStylePatch(initial, colorPatch);

    const reconciled = reconcileDraftContentRunsForCommit({
      draftRuns: whiteRuns,
      containerStyle: afterA.style,
    });
    expect(reconciled?.every((run) => run.style?.color == null)).toBe(true);
    expect(reconciled?.[0]?.text).toBe("PPM INTERNO");
  });

  it("preserva cor de trecho marcada como edição explícita", () => {
    const draftRuns = [
      { text: "PPM ", style: { color: "#ffffff" as const } },
      { text: "INTERNO", style: { color: "#dc2626" as const } },
    ];
    const reconciled = reconcileDraftContentRunsForCommit({
      draftRuns,
      containerStyle: { color: "#000000" },
      explicitRunStyleKeys: new Set(["color"]),
    });
    expect(reconciled?.[0]?.style?.color).toBe("#ffffff");
    expect(reconciled?.[1]?.style?.color).toBe("#dc2626");
  });

  it("família irmã: fontSize de container remove override stale nos runs", () => {
    const draftRuns = [
      { text: "Título", style: { fontSize: 56, color: "#ffffff" as const } },
    ];
    const reconciled = reconcileDraftContentRunsForCommit({
      draftRuns,
      containerStyle: { fontSize: 32, color: "#0f172a" },
    });
    expect(reconciled?.[0]?.style?.fontSize).toBeUndefined();
    expect(reconciled?.[0]?.style?.color).toBeUndefined();
    expect(reconciled?.[0]?.text).toBe("Título");
  });

  it("negativo: sem tipografia de container o draft permanece intacto", () => {
    const draftRuns = [{ text: "X", style: { color: "#ffffff" as const } }];
    const reconciled = reconcileDraftContentRunsForCommit({
      draftRuns,
      containerStyle: { zIndex: 2, borderRadius: 4 },
    });
    expect(reconciled).toEqual(draftRuns);
  });

  it("containerTypographyKeysFromRunPatch espelha o patch parcial", () => {
    expect(containerTypographyKeysFromRunPatch({ color: "#000000", fontSize: 20 })).toEqual([
      "fontSize",
      "color",
    ]);
  });

  it("cores irmãs: preto, azul-escuro, vermelho e branco no container", () => {
    for (const color of ["#000000", "#1e3a5f", "#7f1d1d", "#ffffff"]) {
      const after = applyComunicadoBlockStylePatch(
        shapeBlock(),
        sparsePropertyPatch(fillToColorStylePatch({ kind: "solid", color })),
      );
      const reconciled = reconcileDraftContentRunsForCommit({
        draftRuns: whiteRuns,
        containerStyle: after.style,
      });
      expect(after.style?.color).toBe(color);
      expect(reconciled?.every((run) => run.style?.color == null)).toBe(true);
    }
  });
});
