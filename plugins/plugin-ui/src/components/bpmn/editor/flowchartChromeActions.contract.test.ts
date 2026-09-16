import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("flowchart chrome actions contract", () => {
  it("expõe chromeActions no editor e move sync Mermaid para o head", () => {
    const editor = readFileSync(join(here, "FlowchartEditor.tsx"), "utf8");
    const toolbar = readFileSync(join(here, "FlowchartEditorToolbar.tsx"), "utf8");
    const mermaid = readFileSync(join(here, "../mermaid/FlowchartMermaidPanel.tsx"), "utf8");

    expect(editor).toMatch(/chromeActions\?:/);
    expect(toolbar).toMatch(/chromeActions/);
    expect(toolbar).toMatch(/mermaidControls/);
    expect(toolbar).toMatch(/mermaidRefreshFromDrawing/);
    expect(mermaid).toMatch(/showToolbar\?:/);
    expect(mermaid).toMatch(/viewportLabels=\{labels\}/);
    expect(editor).not.toMatch(/style=\{\{\s*height:\s*canvasHeight/);
    expect(editor).toMatch(/zoomOnScroll/);
    expect(editor).toMatch(/zoomOnPinch/);
    expect(editor).toMatch(/preventScrolling/);
    expect(editor).toMatch(/DIAGRAM_USER_ZOOM_EXTENT/);
    expect(editor).toMatch(/viewportIntentRef/);
    expect(editor).toMatch(/onViewportIntent/);
  });
});
