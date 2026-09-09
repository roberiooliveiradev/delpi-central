import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("AdminDataTable", () => {
  it("aceita headerHint e envolve o cabeçalho com HelpTooltip", () => {
    const source = readFileSync(join(here, "AdminDataTable.tsx"), "utf8");
    expect(source).toMatch(/headerHint\?: string/);
    expect(source).toMatch(/HelpTooltip/);
    expect(source).toMatch(/column\.headerHint/);
  });
});
