import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const css = readFileSync(resolve(process.cwd(), "src/index.css"), "utf8");

function colorToken(name: string): string {
  const match = css.match(new RegExp(name + ":\\s*(#[\\da-fA-F]{6})\\s*;"));
  if (!match) throw new Error("Token de contraste não encontrado: " + name);
  return match[1];
}

function luminance(hex: string): number {
  const rgb = [1, 3, 5].map((index) => {
    const value = parseInt(hex.slice(index, index + 2), 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
}

function contrast(foreground: string, background: string): number {
  const lightness = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (lightness[0] + 0.05) / (lightness[1] + 0.05);
}

describe("contraste do header immersive do Portal de TI", () => {
  it("mantém contraste WCAG AA de texto na busca e nos cinco tons de badge", () => {
    const pairs = [
      ["--itp-hero-search-foreground", "--itp-hero-search-background"],
      ["--itp-hero-search-muted", "--itp-hero-search-background"],
      ...(["neutral", "info", "success", "warning", "danger"] as const).map(
        (tone) => [
          "--itp-hero-badge-" + tone + "-foreground",
          "--itp-hero-badge-" + tone + "-background",
        ],
      ),
    ];

    for (const [foreground, background] of pairs) {
      expect(
        contrast(colorToken(foreground), colorToken(background)),
        foreground + " sobre " + background,
      ).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("mantém escopo apenas do Portal e rótulo da busca visível no mobile", () => {
    expect(css).toContain(".dashboard-it-portal .itp-page-hero--immersive .itp-topbar-search");
    expect(css).toContain(".dashboard-it-portal .itp-page-hero--immersive .itp-topbar-search__label");
    expect(css).toContain(".dashboard-it-portal .itp-page-hero--immersive .itp-status-badge");
    expect(css).toContain(':root[data-theme="dark"] .dashboard-it-portal .itp-topbar .itp-topbar-search');

    const mobile = css.slice(css.indexOf("/* O kit oculta rotulos da TopBar no mobile;"));
    expect(mobile).toContain("position: static;");
    expect(mobile).toContain("clip: auto;");
    expect(mobile).toContain("width: 100%;");
  });
});
