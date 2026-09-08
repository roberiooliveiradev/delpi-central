import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const css = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "data-table.css"),
  "utf8",
);

describe("data-table.css — colunas numéricas", () => {
  it("padding-inline numérico vence o shorthand de th/td (especificidade ≥ table+th+class)", () => {
    // Positive: seletor com table + th/td + col--numeric (não só .col--numeric).
    expect(css).toMatch(
      /table\.delpi-ui-table\s+th\.delpi-ui-table__col--numeric[\s\S]*?padding-inline:\s*var\(--delpi-ui-table-numeric-pad-x/,
    );
    expect(css).toMatch(
      /table\.delpi-ui-table\s+td\.delpi-ui-table__col--numeric[\s\S]*?padding-inline:\s*var\(--delpi-ui-table-numeric-pad-x/,
    );

    // Sibling: align=right sem col--numeric também recebe respiro.
    expect(css).toMatch(
      /th\[data-align="right"\]:not\(\.delpi-ui-table__col--numeric\)[\s\S]*?padding-inline:\s*var\(--delpi-ui-table-numeric-pad-x/,
    );

    // Negative: regra fraca (só classe) que o shorthand de th/td sobrescrevia.
    expect(css).not.toMatch(/(?:^|\n)\.delpi-ui-table__col--numeric\s*\{/);
  });
});
