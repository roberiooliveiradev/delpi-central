import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const SOURCE = readFileSync(
  resolve(process.cwd(), "src/components/DataPrepareModal.tsx"),
  "utf8",
);

describe("DataPrepareModal — baseline transacional da Fase 0", () => {
  it("caracteriza que editar etapas persiste imediatamente", () => {
    expect(SOURCE).toMatch(
      /const persistSteps[\s\S]*updateBlock\(active\.id,\s*\{\s*dataTransform:\s*transform/,
    );
    expect(SOURCE).toMatch(/const addStep[\s\S]*persistSteps\(\[\.\.\.steps,\s*step\]\)/);
    expect(SOURCE).toMatch(/const replaceStep[\s\S]*persistSteps\(next\)/);
  });

  it("caracteriza que Cancelar apenas fecha e Aplicar força refresh", () => {
    expect(SOURCE).toMatch(/>\s*Cancelar\s*<\/button>/);
    expect(SOURCE).toMatch(/onClick=\{onClose\}[\s\S]*>\s*Cancelar/);
    expect(SOURCE).toMatch(
      /const handleCloseAndApply[\s\S]*refreshDataPreview\([\s\S]*force:\s*true[\s\S]*onClose\(\)/,
    );
  });
});
