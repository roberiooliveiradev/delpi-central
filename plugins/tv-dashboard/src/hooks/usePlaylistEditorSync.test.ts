import { describe, expect, it, vi } from "vitest";

import { usePlaylistEditorSync } from "./usePlaylistEditorSync";

vi.mock("@delpi/tv-dashboard-presentation", () => ({
  buildAdminPresentationWsUrl: (playlistId: string, token: string) =>
    `ws://test/${playlistId}?access_token=${token}`,
  usePresentationRealtime: vi.fn(),
}));

describe("usePlaylistEditorSync", () => {
  it("exporta hook de sincronização do editor", () => {
    expect(typeof usePlaylistEditorSync).toBe("function");
  });
});
