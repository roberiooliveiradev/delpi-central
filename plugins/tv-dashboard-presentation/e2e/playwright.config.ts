import { defineConfig, devices } from "@playwright/test";

/** E2E visual capture — Issue #129 / DI-VISUAL.
 * Renderiza o palco canônico tv-dashboard/present (shared
 * Presentation Package) em 1920x1080 e salva screenshot real.
 * baseURL/token via env — nunca commitar credenciais:
 *   TV_PRESENT_BASE_URL   (ex.: https://hub.delpi...)
 *   TV_PRESENT_TOKEN      (share público governado)
 * Artifacts ficam em e2e/artifacts (gitignored). */
export default defineConfig({
  testDir: "./specs",
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  outputDir: "./artifacts/test-results",
  use: {
    baseURL: process.env.TV_PRESENT_BASE_URL ?? "http://localhost",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: [
    {
      name: "tv-1080p",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1920, height: 1080 },
      },
    },
  ],
});
