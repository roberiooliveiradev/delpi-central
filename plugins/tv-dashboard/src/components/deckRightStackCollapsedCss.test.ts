import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Regressão: notas do apresentador no right-stack forçavam largura com o
 * inspetor recolhido (trilho estreito + coluna vazia à direita).
 */
describe("deck right-stack collapsed CSS", () => {
  const css = readFileSync(
    resolve(dirname(fileURLToPath(import.meta.url)), "../index.css"),
    "utf8",
  );

  it("restringe o right-stack a 36px quando o painel está recolhido", () => {
    expect(css).toMatch(
      /\.td-deck-right-stack:has\(\.td-deck-side-panel--collapsed\)\s*\{[^}]*width:\s*36px/s,
    );
  });

  it("esconde notas do apresentador com o painel recolhido (legado CSS)", () => {
    expect(css).toMatch(
      /\.td-deck-right-stack:has\(\.td-deck-side-panel--collapsed\) \.td-deck-speaker-notes\s*\{[^}]*display:\s*none/s,
    );
  });

  it("layout do editor não monta o campo de notas do apresentador", () => {
    const layout = readFileSync(
      resolve(dirname(fileURLToPath(import.meta.url)), "./CustomSlideEditorLayout.tsx"),
      "utf8",
    );
    expect(layout).not.toMatch(/td-speaker-notes|Notas do apresentador|td-deck-speaker-notes/);
  });

  it("fixa largura do painel stage recolhido em 36px (não herda width aberto)", () => {
    expect(css).toMatch(
      /\.td-deck-side-panel--stage\.td-deck-side-panel--collapsed\s*\{[^}]*width:\s*36px[^}]*min-width:\s*36px[^}]*max-width:\s*36px/s,
    );
  });
});
