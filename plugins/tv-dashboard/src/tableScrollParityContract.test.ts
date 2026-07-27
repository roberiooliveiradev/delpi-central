import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

function ruleBody(css: string, selector: string): string {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = css.match(new RegExp(`(^|[\\s}])${escaped}\\s*\\{([\\s\\S]*?)\\}`, "m"));
  return match?.[2] ?? "";
}

/**
 * Contrato editor ↔ /present/ — scroll da table_view.
 *
 * Anti-padrão: depender do `* { scrollbar-width: thin }` global do portal
 * (public-hub não tem) ou `touch-action: none` no wrap da tabela sem exceção.
 */
describe("table scroll parity contract (editor ↔ TV)", () => {
  it("frame canônico declara scrollbar thin; wrap da tabela libera pan", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const kitCss = readFileSync(
      join(here, "../../plugin-ui/src/styles/configurable-table.css"),
      "utf8",
    );
    const presentationCss = readFileSync(
      join(here, "../../tv-dashboard-presentation/src/native-screens.css"),
      "utf8",
    );
    const editorCss = readFileSync(join(here, "index.css"), "utf8");
    const composerSrc = readFileSync(
      join(here, "components/ComunicadoComposer.tsx"),
      "utf8",
    );

    const kitFrame = ruleBody(kitCss, ".delpi-ui-config-table__frame");
    expect(kitFrame).toMatch(/overflow:\s*auto/);
    expect(kitFrame).toMatch(/scrollbar-width:\s*thin/);
    expect(kitFrame).toMatch(/touch-action:\s*pan-x\s+pan-y/);

    const tvFrame = ruleBody(presentationCss, ".tdp-table-frame");
    expect(tvFrame).toMatch(/overflow:\s*auto/);
    expect(tvFrame).toMatch(/scrollbar-width:\s*thin/);
    expect(tvFrame).toMatch(/touch-action:\s*pan-x\s+pan-y/);

    const tableWrap = ruleBody(
      editorCss,
      ".dashboard-tv-dashboard .td-composer__block-wrap--table",
    );
    expect(tableWrap).toMatch(/touch-action:\s*pan-x\s+pan-y/);
    expect(composerSrc).toMatch(/td-composer__block-wrap--table/);
  });
});
