import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { CSSProperties } from "react";
import { describe, expect, it } from "vitest";

import { resolveBlockShapeChromeBoxShadow } from "./comunicadoBlockShapeChrome";
import {
  blockCssStyle,
  createTableViewBlock,
  parseComunicadoConfig,
} from "./comunicadoHelpers";
import { getTablePartState, resolveTableFrameStyle } from "./comunicadoTableParts";
import type { ComunicadoTableViewBlock } from "./comunicadoTypes";

/**
 * TV-TABLE-SHADOW-001 — sombra da moldura de `table_view` tem autoridade única:
 * `tableParts.frame.style.boxShadow` (paint via --tdp-table-frame-shadow).
 * `block.style.boxShadow` legado só participa de load/migração.
 */
const LEGACY_SHADOW = "0 8px 24px rgba(0, 0, 0, 0.35)";
const NONE_SENTINEL = "none";

function rawTableView(styleExtra?: Record<string, unknown>, tableParts?: unknown) {
  return {
    id: "t1",
    type: "table_view",
    frame: { x: 5, y: 20, w: 60, h: 30 },
    style: { zIndex: 2, ...styleExtra },
    tableParts,
    dataBinding: { operationId: "op", params: {} },
  };
}

describe("table frame shadow authority", () => {
  it("incidente: frame 'none' + block.style legado → menu 'Nenhuma' e paint sem sombra", () => {
    const parsed = parseComunicadoConfig({
      blocks: [
        rawTableView(
          { boxShadow: LEGACY_SHADOW },
          { frame: { visible: true, style: { boxShadow: NONE_SENTINEL } } },
        ),
      ],
    });
    const block = (parsed.blocks ?? [])[0] as ComunicadoTableViewBlock;
    /* Menu (Forma/Sombra e Design da Tabela) lê a sombra efetiva do frame. */
    expect(resolveBlockShapeChromeBoxShadow(block)).toBeUndefined();
    /* Wrapper não emite a var legada que sobrepunha a moldura. */
    const css = blockCssStyle(block) as CSSProperties & Record<string, string>;
    expect(css["--tdp-block-box-shadow"]).toBeUndefined();
    expect(css.boxShadow).toBeUndefined();
    /* Frame persistido continua "none". */
    expect(getTablePartState(block.tableParts, { kind: "frame" })?.style?.boxShadow).toBe(
      NONE_SENTINEL,
    );
    expect(resolveTableFrameStyle(block.tableParts).boxShadow).toBe(NONE_SENTINEL);
  });

  it("load migra block.style.boxShadow legado → frame (menu == paint == persistido)", () => {
    const parsed = parseComunicadoConfig({
      blocks: [rawTableView({ boxShadow: LEGACY_SHADOW })],
    });
    const block = (parsed.blocks ?? [])[0] as ComunicadoTableViewBlock;
    expect(getTablePartState(block.tableParts, { kind: "frame" })?.style?.boxShadow).toBe(
      LEGACY_SHADOW,
    );
    expect(resolveBlockShapeChromeBoxShadow(block)).toBe(LEGACY_SHADOW);
    expect(resolveTableFrameStyle(block.tableParts).boxShadow).toBe(LEGACY_SHADOW);
  });

  it("round-trip: 'none' explícito sobrevive serialize → parse → menu/paint", () => {
    const block = createTableViewBlock(3, 3) as ComunicadoTableViewBlock;
    const cleared: ComunicadoTableViewBlock = {
      ...block,
      tableParts: {
        ...(block.tableParts ?? {}),
        frame: {
          ...(block.tableParts?.frame ?? {}),
          style: { ...(block.tableParts?.frame?.style ?? {}), boxShadow: NONE_SENTINEL },
        },
      },
      style: { ...block.style },
    };
    const reloaded = (parseComunicadoConfig({
      blocks: [JSON.parse(JSON.stringify(cleared))],
    }).blocks ?? [])[0] as ComunicadoTableViewBlock;
    expect(getTablePartState(reloaded.tableParts, { kind: "frame" })?.style?.boxShadow).toBe(
      NONE_SENTINEL,
    );
    expect(resolveBlockShapeChromeBoxShadow(reloaded)).toBeUndefined();
    expect(resolveTableFrameStyle(reloaded.tableParts).boxShadow).toBe(NONE_SENTINEL);
  });

  it("round-trip: sombra custom do frame sobrevive e é a efetiva", () => {
    const custom = "0 2px 6px rgba(9, 30, 66, 0.4), 0 12px 30px rgba(9, 30, 66, 0.2)";
    const block = createTableViewBlock(3, 3) as ComunicadoTableViewBlock;
    const withCustom: ComunicadoTableViewBlock = {
      ...block,
      tableParts: {
        ...(block.tableParts ?? {}),
        frame: {
          ...(block.tableParts?.frame ?? {}),
          style: { ...(block.tableParts?.frame?.style ?? {}), boxShadow: custom },
        },
      },
    };
    const reloaded = (parseComunicadoConfig({
      blocks: [JSON.parse(JSON.stringify(withCustom))],
    }).blocks ?? [])[0] as ComunicadoTableViewBlock;
    expect(resolveBlockShapeChromeBoxShadow(reloaded)).toBe(custom);
    expect(resolveTableFrameStyle(reloaded.tableParts).boxShadow).toBe(custom);
  });

  it("CSS: table_view pinta sombra só via --tdp-table-frame-shadow", () => {
    const nativeCss = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "native-screens.css"),
      "utf8",
    );
    /* Base da tabela tdp não lê a var legada de bloco. */
    expect(nativeCss).toMatch(
      /\.tdp-configurable-table\s*\{[^}]*box-shadow:\s*var\(\s*--tdp-table-frame-shadow,\s*none\s*\)/s,
    );

    /* table_view (comunicado): regra escopada ao frame no CSS do palco. */
    const stageCss = readFileSync(
      join(
        dirname(fileURLToPath(import.meta.url)),
        "../../plugin-ui/src/styles/comunicado-stage.css",
      ),
      "utf8",
    );
    expect(stageCss).toContain(
      ".delpi-ui-comunicado__block--table-view .tdp-data-block--table .tdp-configurable-table",
    );
    expect(stageCss).toMatch(
      /\.tdp-configurable-table,\s*\n\.delpi-ui-comunicado__block--table_view\s+\.tdp-data-block--table\s+\.tdp-configurable-table\s*\{\s*box-shadow:\s*var\(\s*--tdp-table-frame-shadow,\s*none\s*\)/s,
    );

    const kitCss = readFileSync(
      join(
        dirname(fileURLToPath(import.meta.url)),
        "../../plugin-ui/src/styles/configurable-table.css",
      ),
      "utf8",
    );
    /* Variante delpi-ui: nenhuma regra de tabela pinta via var legada. */
    expect(kitCss).not.toMatch(
      /\.delpi-ui-config-table[^{]*\{[^}]*box-shadow:\s*var\(\s*--tdp-block-box-shadow/s,
    );
  });
});
