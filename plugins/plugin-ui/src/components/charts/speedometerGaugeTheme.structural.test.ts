import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const cssPath = join(
  dirname(fileURLToPath(import.meta.url)),
  "../../styles/speedometer-gauge.css",
);

describe("speedometer-gauge.css theme tokens", () => {
  const css = readFileSync(cssPath, "utf8");

  it("tooltip usa cadeia title→text com fallback escuro-legível em claro", () => {
    expect(css).toMatch(
      /\.delpi-ui-speedometer-gauge__tooltip[\s\S]*?color:\s*var\(\s*--delpi-ui-title,\s*var\(\s*--delpi-ui-text/,
    );
    expect(css).not.toMatch(
      /\.delpi-ui-speedometer-gauge__tooltip[\s\S]*?color:\s*var\(\s*--delpi-ui-title,\s*#f8fafc\s*\)/,
    );
  });

  it("não aplica wash de hover/focus que muda a cor do card (paridade com séries)", () => {
    expect(css).not.toMatch(
      /\.delpi-ui-speedometer-gauge:not\(\[data-interactive="true"\]\):hover/,
    );
    expect(css).not.toMatch(
      /speedometer-gauge:not\(\[data-interactive="true"\]\):hover[\s\S]*?background:\s*color-mix/,
    );
    expect(css).toMatch(/\.delpi-ui-speedometer-gauge:focus-visible/);
    expect(css).toMatch(/outline:\s*2px solid/);
  });

  it("fill do arco não usa glow permanente (evita parecer hover)", () => {
    expect(css).toMatch(
      /\.delpi-ui-speedometer-gauge__fill\s*\{[^}]*filter:\s*none/s,
    );
  });
});
