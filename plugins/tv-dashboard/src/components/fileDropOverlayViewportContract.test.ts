import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("file drop overlay viewport contract", () => {
  it("overlay fica no slot (fora do scroll), centralizado na página visível", () => {
    const shell = readFileSync(join(here, "ComunicadoStageShell.tsx"), "utf8");
    const css = readFileSync(join(here, "../index.css"), "utf8");

    expect(shell).toContain('className={[\n            "td-composer__canvas-slot"');
    expect(shell).toContain("td-composer__file-drop-overlay");
    // Overlay é irmão do wrap (depois de fechar o wrap), não filho do scroll.
    const wrapCloseThenOverlay = shell.indexOf("{children}");
    const overlayIdx = shell.indexOf("td-composer__file-drop-overlay");
    const wrapCloseAfterChildren = shell.indexOf("</div>", wrapCloseThenOverlay);
    expect(overlayIdx).toBeGreaterThan(wrapCloseAfterChildren);

    expect(css).toMatch(/\.td-composer__canvas-slot\s*\{/);
    expect(css).toMatch(
      /\.td-composer__file-drop-overlay\s*\{[^}]*place-items:\s*center/s,
    );
    expect(css).toMatch(
      /\.td-stage-shell__workspace--rulers\s+\.td-composer__canvas-slot\s*\{[^}]*grid-column:\s*2/s,
    );
  });
});
