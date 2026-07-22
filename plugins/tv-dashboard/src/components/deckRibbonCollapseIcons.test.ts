import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { Type } from "lucide-react";

import {
  DECK_RIBBON_COLLAPSE_ICONS,
  resolveDeckRibbonCollapseIcon,
} from "./deck/deckRibbonCollapseIcons";

function walkTsx(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) walkTsx(full, out);
    else if (name.endsWith(".tsx") || name.endsWith(".ts")) out.push(full);
  }
  return out;
}

describe("deckRibbonCollapseIcons", () => {
  it("resolveDeckRibbonCollapseIcon usa override e mapa", () => {
    expect(resolveDeckRibbonCollapseIcon("typo-font")).toBe(DECK_RIBBON_COLLAPSE_ICONS["typo-font"]);
    expect(resolveDeckRibbonCollapseIcon("typo-font", Type)).toBe(Type);
    expect(resolveDeckRibbonCollapseIcon("desconhecido")).toBeUndefined();
    expect(resolveDeckRibbonCollapseIcon(undefined)).toBeUndefined();
  });

  it("slide-current e playlist-chrome não usam Eye", () => {
    expect(DECK_RIBBON_COLLAPSE_ICONS["slide-current"]).not.toBe(
      DECK_RIBBON_COLLAPSE_ICONS["view-show"],
    );
    expect(DECK_RIBBON_COLLAPSE_ICONS["playlist-chrome"]).not.toBe(
      DECK_RIBBON_COLLAPSE_ICONS["view-show"],
    );
  });

  it("todo groupId=\"…\" explícito em componentes tem ícone no mapa", () => {
    const root = resolve(__dirname);
    const files = walkTsx(root).filter(
      (f) => !f.includes(".test.") && !f.endsWith("deckRibbonCollapseIcons.ts"),
    );
    const ids = new Set<string>();
    const re = /groupId\s*=\s*"([^"]+)"/g;
    for (const file of files) {
      const text = readFileSync(file, "utf8");
      if (!text.includes("DeckRibbonGroup") && !text.includes("groupId=")) continue;
      let m: RegExpExecArray | null;
      while ((m = re.exec(text))) {
        ids.add(m[1]);
      }
    }
    expect(ids.size).toBeGreaterThan(20);
    const missing = [...ids].filter((id) => !DECK_RIBBON_COLLAPSE_ICONS[id]).sort();
    expect(missing).toEqual([]);
  });

  it("DeckRibbonGroup resolve ícone via mapa", () => {
    const src = readFileSync(resolve(__dirname, "./deck/DeckRibbonGroup.tsx"), "utf8");
    expect(src).toContain("resolveDeckRibbonCollapseIcon");
  });
});
