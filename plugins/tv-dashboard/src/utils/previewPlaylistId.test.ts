import { describe, expect, it } from "vitest";

import { resolvePreviewPlaylistId } from "./previewPlaylistId";

describe("resolvePreviewPlaylistId", () => {
  it("returns real playlist UUIDs", () => {
    expect(resolvePreviewPlaylistId("550e8400-e29b-41d4-a716-446655440000")).toBe(
      "550e8400-e29b-41d4-a716-446655440000",
    );
  });

  it("omits template-library sentinel (editor de template)", () => {
    expect(resolvePreviewPlaylistId("template-library")).toBeUndefined();
  });

  it("omits empty and non-uuid values", () => {
    expect(resolvePreviewPlaylistId("")).toBeUndefined();
    expect(resolvePreviewPlaylistId("   ")).toBeUndefined();
    expect(resolvePreviewPlaylistId(null)).toBeUndefined();
    expect(resolvePreviewPlaylistId(undefined)).toBeUndefined();
    expect(resolvePreviewPlaylistId("not-a-uuid")).toBeUndefined();
  });
});
