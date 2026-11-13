import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("invoicePostingApi API_BASE", () => {
  it("default source string is the BFF path", () => {
    const source = readFileSync(join(here, "invoicePostingApi.ts"), "utf8");
    expect(source).toContain(
      '"/apps/controllership-finance-api/lancamento-notas-fiscais"',
    );
    expect(source).not.toContain('"/apps/api-delpi/lancamento-notas-fiscais"');
    expect(source).toContain("VITE_LNF_API_BASE");
  });
});
