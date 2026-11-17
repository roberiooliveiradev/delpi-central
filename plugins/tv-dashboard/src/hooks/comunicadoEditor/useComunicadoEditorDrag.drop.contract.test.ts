import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const hookDir = dirname(fileURLToPath(import.meta.url));
const drag = readFileSync(join(hookDir, "useComunicadoEditorDrag.ts"), "utf8");
const interaction = readFileSync(
  join(hookDir, "../../components/useCanvasBlockInteraction.ts"), "utf8",
);
const stage = readFileSync(join(hookDir, "useComunicadoEditorStage.ts"), "utf8");

describe("GLPI #1612 | release no ponto real do ponteiro", () => {
  it("aplica a última coordenada antes de finalizar no pointerup", () => {
    expect(interaction).toMatch(
      /onPointerUp = \(event: PointerEvent\) => \{[\s\S]*?applyDragMoveRef\.current\(event\);\s*finishInteraction\(\);/,
    );
  });

  it("não reverte o encaixe em objetos ao aplicar encaixe na grade em um grupo", () => {
    expect(drag).toMatch(
      /\{ \.\.\.anchor, frame: finalGesture\.group\.frame \}/,
    );
    expect(drag).toMatch(
      /finalGesture = \{\s*\.\.\.finalGesture,\s*group: \{ \.\.\.finalGesture\.group, frame: snappedGroup \}/,
    );
  });

  it("sincroniza o estado dos ímãs com os refs usados durante o gesto", () => {
    expect(stage).toMatch(
      /snapToGridRef\.current = next;\s*patchPrefs\(\{ snapToGrid: next \}\)/,
    );
    expect(stage).toMatch(
      /snapToObjectsRef\.current = next;\s*patchPrefs\(\{ snapToObjects: next \}\)/,
    );
  });
});
