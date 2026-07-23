import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const base = dirname(fileURLToPath(import.meta.url));

describe("canvas drag persist contract", () => {
  it("live do gesto não dispara autosave; commit só no pointerup", () => {
    const dragSrc = readFileSync(join(base, "useComunicadoEditorDrag.ts"), "utf8");
    const ctxSrc = readFileSync(join(base, "../../components/comunicadoEditorContext.tsx"), "utf8");
    expect(dragSrc).toMatch(/persist:\s*false/);
    expect(ctxSrc).toMatch(/options\?\.persist === false/);
    expect(ctxSrc).toMatch(/updateBlockLive[\s\S]*persist:\s*false/);
    expect(ctxSrc).toMatch(/enableHistoryShortcuts:\s*true/);
  });
});
