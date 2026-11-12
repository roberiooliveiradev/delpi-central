import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const css = readFileSync(resolve(process.cwd(), "src/index.css"), "utf8");

function tokenColor(token: string): string {
  const match = css.match(new RegExp(`--${token}:\\s*(#[0-9a-fA-F]{6})\\s*;`));
  if (!match) throw new Error(`Token de contraste nao encontrado: ${token}`);
  return match[1];
}

function luminance(hex: string): number {
  const channels = [1, 3, 5]
    .map((index) => Number.parseInt(hex.slice(index, index + 2), 16) / 255)
    .map((value) => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrastRatio(first: string, second: string): number {
  const [light, dark] = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (light + 0.05) / (dark + 0.05);
}

describe("Portal de TI immersive header: accessibility contrast", () => {
  it("keeps white text readable over search and all badge backgrounds (WCAG AA)", () => {
    for (const token of [
      "itp-hero-search-bg",
      "itp-hero-search-hover",
      "itp-hero-badge-neutral-bg",
      "itp-hero-badge-info-bg",
      "itp-hero-badge-success-bg",
      "itp-hero-badge-warning-bg",
      "itp-hero-badge-danger-bg",
    ]) {
      expect(contrastRatio("#ffffff", tokenColor(token)), token).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("uses a navy header background in both light and dark themes", () => {
    expect(css).toMatch(/:root\[data-theme="dark"\] \.dashboard-it-portal \.itp-page-hero--immersive/);
    expect(css).toMatch(/\.dashboard-it-portal \.itp-page-hero--immersive,[\s\S]*?linear-gradient\(115deg, #06243d 0%, #073c5e 55%, #085476 100%\)/);
    expect(contrastRatio("#ffffff", "#085476")).toBeGreaterThanOrEqual(4.5);
  });

  it("scopes search and badges to immersive hero without altering the main top bar", () => {
    expect(css).toMatch(/\.itp-page-hero--immersive \.itp-topbar-search\s*\{/);
    expect(css).toMatch(/\.itp-page-hero--immersive \.itp-topbar-search__kbd\s*\{/);
    expect(css).toMatch(/\.itp-page-hero--immersive \.itp-topbar-search:focus-visible\s*\{/);
    expect(css).toMatch(/\.itp-page-hero--immersive \.itp-page-hero__badge \.itp-status-badge\s*\{/);
    for (const variant of ["info", "success", "warning", "danger"]) {
      expect(css).toContain(`itp-page-hero__badge .itp-status-badge--${variant}`);
    }
  });
});
