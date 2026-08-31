import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  PRESENTATION_SYNC_FOCUS_SLIDE_REASONS,
  resolvePresentationSyncFocusSlideId,
} from "./presentationSyncFocusSlide";

describe("resolvePresentationSyncFocusSlideId", () => {
  it("não foca em slide_updated (autosave / peer em outro slide)", () => {
    expect(
      resolvePresentationSyncFocusSlideId({
        reason: "slide_updated",
        slideId: "slide-peer",
      }),
    ).toBeNull();
  });

  it("não foca em reorder, delete, media nem reconnect sem evento", () => {
    expect(
      resolvePresentationSyncFocusSlideId({
        reason: "slides_reordered",
        slideId: "slide-a",
      }),
    ).toBeNull();
    expect(
      resolvePresentationSyncFocusSlideId({
        reason: "slide_deleted",
        slideId: "slide-gone",
      }),
    ).toBeNull();
    expect(
      resolvePresentationSyncFocusSlideId({
        reason: "media_uploaded",
        slideId: "slide-a",
      }),
    ).toBeNull();
    expect(resolvePresentationSyncFocusSlideId(undefined)).toBeNull();
    expect(resolvePresentationSyncFocusSlideId(null)).toBeNull();
  });

  it("foca só em reasons de criação/import/duplicação com slideId", () => {
    for (const reason of PRESENTATION_SYNC_FOCUS_SLIDE_REASONS) {
      expect(
        resolvePresentationSyncFocusSlideId({ reason, slideId: "new-slide" }),
        reason,
      ).toBe("new-slide");
    }
    expect(
      resolvePresentationSyncFocusSlideId({
        reason: "slide_created",
        slideId: "  ",
      }),
    ).toBeNull();
  });

  it("não re-seleciona o slide já ativo", () => {
    expect(
      resolvePresentationSyncFocusSlideId(
        { reason: "slide_created", slideId: "slide-a" },
        { currentSlideId: "slide-a" },
      ),
    ).toBeNull();
    expect(
      resolvePresentationSyncFocusSlideId(
        { reason: "slide_duplicated", slideId: "slide-b" },
        { currentSlideId: "slide-a" },
      ),
    ).toBe("slide-b");
  });
});

describe("PlaylistEditorPage wire (contrato)", () => {
  it("usa resolvePresentationSyncFocusSlideId no onSync — não focusSlideId cru do evento", () => {
    const page = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "../pages/PlaylistEditorPage.tsx"),
      "utf8",
    );
    expect(page).toContain('from "../utils/presentationSyncFocusSlide"');
    expect(page).toContain("resolvePresentationSyncFocusSlideId(event");
    expect(page).not.toMatch(
      /reloadPlaylistFromServer\(\{\s*focusSlideId:\s*event\?\.slideId/,
    );
  });
});
