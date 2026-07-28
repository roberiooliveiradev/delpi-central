import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("editor presence disconnect criteria", () => {
  it("sync de presença respeita editorActive (não segura socket fora do editor)", () => {
    const page = readFileSync(join(here, "../pages/PlaylistEditorPage.tsx"), "utf8");
    expect(page).toMatch(/usePlaylistEditorSync\(\{[\s\S]*enabled:\s*editorActive/);
  });

  it("realtime tem guarda de path SPA além de pagehide", () => {
    const realtime = readFileSync(
      join(here, "../../../tv-dashboard-presentation/src/usePresentationRealtime.ts"),
      "utf8",
    );
    expect(realtime).toContain("guardPortalPath");
    expect(realtime).toContain("isTvDashboardPortalPath");
    expect(realtime).toContain("tearDownPresenceSocket");
  });

  it("bootstrap unmount funciona sem el (fallback lastMounted)", () => {
    const boot = readFileSync(join(here, "../bootstrap.tsx"), "utf8");
    expect(boot).toContain("lastMountedEl");
    expect(boot).toMatch(/unmount\(el\?:\s*HTMLElement/);
  });
});
