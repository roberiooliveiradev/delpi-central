import { test, expect } from "@playwright/test";
import { mkdirSync } from "node:fs";

/** Captura visual do palco canônico (Issue #129).
 * Requer TV_PRESENT_TOKEN (share público do LAB) — sem token,
 * o spec falha explicitamente, nunca vira VISUAL_PASS. */
const TOKEN = process.env.TV_PRESENT_TOKEN ?? "";
const OUT = "./artifacts/captures";

test("tv present 1920x1080 — capture", async ({ page }) => {
  expect(TOKEN, "TV_PRESENT_TOKEN ausente").not.toBe("");
  await page.goto("/tv-dashboard/present?token=" + TOKEN);
  await page.waitForSelector(
    "[data-testid=\"presentation-stage\"], canvas, svg, main",
    { timeout: 30_000 },
  );
  await page.waitForLoadState("networkidle", { timeout: 20_000 });
  mkdirSync(OUT, { recursive: true });
  await page.screenshot({
    path: OUT + "/tv-present-1080p.png",
    fullPage: false,
  });
  const title = await page.title();
  expect(title.length).toBeGreaterThan(0);
});
