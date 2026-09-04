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

  it("hover não usa wash só de border escuro (legível em claro)", () => {
    expect(css).toMatch(/--delpi-ui-accent[\s\S]*?10%/);
    expect(css).not.toMatch(
      /speedometer-gauge:not\(\[data-interactive="true"\]\):hover[\s\S]*?#334155\)\s*28%/,
    );
  });
});
