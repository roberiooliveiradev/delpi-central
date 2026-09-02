#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { splitManualTextWithToolLinks } from "../../content/userManualToolLinks.ts";

describe("splitManualTextWithToolLinks", () => {
  it("intercala Início e Visão geral", () => {
    const parts = splitManualTextWithToolLinks(
      "Na Visão geral — não no Início (o Início é para ação).",
    );
    assert.deepEqual(
      parts.map((p) => [p.kind, p.value, p.kind === "link" ? p.viewId : null]),
      [
        ["text", "Na ", null],
        ["link", "Visão geral", "overview"],
        ["text", " — não no ", null],
        ["link", "Início", "home"],
        ["text", " (o ", null],
        ["link", "Início", "home"],
        ["text", " é para ação).", null],
      ],
    );
  });

  it("prioriza label mais longo em empate de posição", () => {
    const parts = splitManualTextWithToolLinks("Abra Pontualidade (OTD) ou só OTD.");
    assert.equal(parts[0]?.kind, "text");
    assert.equal(parts[1]?.kind, "link");
    assert.equal(parts[1]?.value, "Pontualidade (OTD)");
    assert.equal(parts[3]?.kind, "link");
    assert.equal(parts[3]?.value, "OTD");
  });
});
