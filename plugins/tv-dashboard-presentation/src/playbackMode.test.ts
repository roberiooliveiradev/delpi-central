import { describe, expect, it } from "vitest";

import {
  DEFAULT_PLAYBACK_MODE,
  isAutoAdvanceMode,
  parsePlaybackMode,
  playbackModeLabel,
  resolvePlaybackMode,
} from "./playbackMode";

describe("playbackMode", () => {
  it("parsePlaybackMode aceita presentation e meeting", () => {
    expect(parsePlaybackMode("presentation")).toBe("presentation");
    expect(parsePlaybackMode("MEETING")).toBe("meeting");
    expect(parsePlaybackMode("kiosk")).toBeNull();
    expect(parsePlaybackMode(null)).toBeNull();
  });

  it("resolvePlaybackMode prioriza query → sessão → playlist → default", () => {
    expect(
      resolvePlaybackMode({
        queryMode: "meeting",
        sessionMode: "presentation",
        playlistMode: "presentation",
      }),
    ).toBe("meeting");
    expect(
      resolvePlaybackMode({
        queryMode: null,
        sessionMode: "meeting",
        playlistMode: "presentation",
      }),
    ).toBe("meeting");
    expect(
      resolvePlaybackMode({
        queryMode: null,
        sessionMode: null,
        playlistMode: "meeting",
      }),
    ).toBe("meeting");
    expect(resolvePlaybackMode({})).toBe(DEFAULT_PLAYBACK_MODE);
  });

  it("isAutoAdvanceMode só em presentation", () => {
    expect(isAutoAdvanceMode("presentation")).toBe(true);
    expect(isAutoAdvanceMode("meeting")).toBe(false);
  });

  it("playbackModeLabel em PT-BR", () => {
    expect(playbackModeLabel("presentation")).toBe("Apresentação");
    expect(playbackModeLabel("meeting")).toBe("Reunião");
  });
});
