import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("meeting playback cursor sync contract", () => {
  it("engine expõe syncPlaybackCursor e publica só em navegação local", () => {
    const engine = readFileSync(join(here, "usePresentationEngine.ts"), "utf8");
    expect(engine).toContain("syncPlaybackCursor");
    expect(engine).toContain("playbackClientId");
    expect(engine).toContain("onPlaybackCursor");
    expect(engine).toContain('type: "playback_cursor"');
    expect(engine).toContain("localNavRef");
  });

  it("present e prévia ligam sync só em meeting", () => {
    const preview = readFileSync(
      join(here, "../../tv-dashboard/src/presentation/PresentationPreview.tsx"),
      "utf8",
    );
    const present = readFileSync(
      join(here, "../../public-hub/src/apps/tv-dashboard/PresentationView.tsx"),
      "utf8",
    );
    expect(preview).toContain('syncPlaybackCursor: playbackMode === "meeting"');
    expect(present).toContain('syncPlaybackCursor: playbackMode === "meeting"');
    expect(preview).toContain("resolvePresentationPlaybackClientId");
    expect(present).toContain("resolvePresentationPlaybackClientId");
  });
});
