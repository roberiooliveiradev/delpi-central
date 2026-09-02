import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { CANVAS_TABLE_TRACK_DRAG_THRESHOLD_PX } from "./ComunicadoCanvasTableView";

const here = dirname(fileURLToPath(import.meta.url));

describe("canvas table track drag session (E8.S0)", () => {
  it("exporta threshold de arraste", () => {
    expect(CANVAS_TABLE_TRACK_DRAG_THRESHOLD_PX).toBe(3);
  });

  it("view registra listeners em window e lostpointercapture", () => {
    const source = readFileSync(join(here, "ComunicadoCanvasTableView.tsx"), "utf8");
    expect(source).toContain('window.addEventListener("pointermove"');
    expect(source).toContain('window.addEventListener("pointerup"');
    expect(source).toContain('window.addEventListener("lostpointercapture"');
    expect(source).toContain("finishTrackDrag");
    expect(source).not.toMatch(/onPointerMove=\{onTrackHandlePointerMove\}/);
  });

  it("editor só persiste canvasTableOptions no commit de tracks (nunca frame)", () => {
    const source = readFileSync(
      join(here, "../../tv-dashboard/src/components/ComunicadoEditorBlockView.tsx"),
      "utf8",
    );
    const tracksBlock = source.match(
      /onTracksCommit:\s*\(next\)\s*=>\s*\{[\s\S]*?\},/,
    )?.[0];
    expect(tracksBlock).toBeTruthy();
    expect(tracksBlock).toContain("canvasTableOptions");
    expect(tracksBlock).not.toMatch(/\bframe\b/);
  });
});
