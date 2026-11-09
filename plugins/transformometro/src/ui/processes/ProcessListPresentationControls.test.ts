import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const source = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "ProcessListPresentationControls.tsx"),
  "utf8",
);

describe("ProcessListPresentationControls parts", () => {
  it("expõe parts para composição do hero sem duplicar implementação", () => {
    expect(source).toMatch(/parts\?\: ProcessListPresentationPart\[\]/);
    expect(source).toMatch(/"sort-field"/);
    expect(source).toMatch(/"sort-direction"/);
    expect(source).toMatch(/"view-modes"/);
    expect(source).toMatch(/Maior/);
    expect(source).toMatch(/Menor/);
    expect(source).toMatch(/PROCESSO_LIST_VIEW_MODES/);
  });
});
