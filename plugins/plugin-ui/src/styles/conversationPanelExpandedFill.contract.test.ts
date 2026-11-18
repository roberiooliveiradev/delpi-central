/* FIX-01 EVA-PRC-CONVERSATION-EXPANDED-VERTICAL-FILL — contrato CSS:
 * o modo --expanded remove o clamp de embed do RoomPanel para que a
 * conversa preencha a altura útil do modal; o modo compacto preserva
 * seus limites originais. Validação geométrica real fica no E2E HML. */

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const CSS = readFileSync(
  join(__dirname, "conversation-panel.css"),
  "utf-8",
);

describe("conversation-panel.css — expansão vertical", () => {
  it("modo expandido libera o clamp de embed do RoomPanel", () => {
    const expanded = CSS.slice(CSS.indexOf("--expanded {"));
    expect(expanded).toContain("--delpi-ui-room-panel-height: auto");
    expect(expanded).toContain("--delpi-ui-room-panel-max-height: none");
    expect(expanded).toContain("--delpi-ui-room-panel-min-height: 0");
  });

  it("frame expandido cresce por flex sem teto próprio", () => {
    expect(CSS).toMatch(
      /\.delpi-ui-conversation-panel--expanded\s+\.delpi-ui-conversation-panel__frame\s*\{[^}]*flex:\s*1[^}]*max-height:\s*none/s,
    );
  });

  it("modo compacto preserva os limites vigentes", () => {
    const compact = CSS.slice(
      CSS.indexOf(".delpi-ui-conversation-panel__frame {"),
      CSS.indexOf("--expanded"),
    );
    expect(compact).toContain("min-height: 18rem");
    expect(compact).toContain("max-height: 34rem");
    expect(CSS).toContain("max-height: 26rem"); // regra mobile compacta
  });
});
