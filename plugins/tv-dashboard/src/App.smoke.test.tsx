// @vitest-environment happy-dom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

vi.mock("@delpi/tv-dashboard-presentation", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@delpi/tv-dashboard-presentation")>();
  return {
    ...actual,
    usePresentationRealtime: vi.fn(),
  };
});

vi.mock("./api/tvDashboardApi", () => ({
  activatePlaylist: vi.fn(),
  addSlide: vi.fn(),
  addSlideFromPreset: vi.fn(),
  deactivatePlaylist: vi.fn(),
  deletePlaylist: vi.fn(),
  deleteSlide: vi.fn(),
  duplicateSlide: vi.fn(),
  downloadQrPng: vi.fn(),
  getBranchScope: vi.fn().mockResolvedValue({ branches: [] }),
  getPlaylist: vi.fn().mockResolvedValue({
    id: "test-playlist",
    name: "Teste",
    isActive: false,
    viewportProfile: "16:9",
    slides: [
      {
        id: "slide-1",
        title: "Slide KPI",
        slideType: "native",
        nativeScreenKey: "production_oee_overview",
        nativeConfig: {},
        durationSec: 15,
        sortOrder: 0,
        isActive: true,
      },
    ],
  }),
  getPreviewPayload: vi.fn().mockResolvedValue({ slides: [] }),
  getPresentationStatus: vi.fn().mockResolvedValue({ status: "never" }),
  getUiContent: vi.fn().mockResolvedValue({ admin: {} }),
  listNativeScreens: vi.fn().mockResolvedValue([]),
  listSlidePresets: vi.fn().mockResolvedValue([]),
  regeneratePlaylistToken: vi.fn(),
  reorderSlides: vi.fn(),
  updatePlaylist: vi.fn(),
  updateSlide: vi.fn(),
}));

describe("App smoke", () => {
  it("renderiza editor de playlist sem lançar erro", async () => {
    const onConsoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <App pathname="/apps/tv-dashboard/playlists/test-playlist" getAccessToken={() => "token"} />,
    );

    expect(await screen.findByText(/carregando programação/i)).toBeTruthy();
    expect(await screen.findByText(/teste/i, {}, { timeout: 3000 })).toBeTruthy();

    onConsoleError.mockRestore();
  });

  it("renderiza editor com slide custom_message (ComunicadoEditorProvider)", async () => {
    const { getPlaylist } = await import("./api/tvDashboardApi");
    vi.mocked(getPlaylist).mockResolvedValue({
      id: "test-playlist",
      name: "Comunicado",
      isActive: false,
      viewportProfile: "16:9",
      slides: [
        {
          id: "slide-custom",
          title: "Comunicado",
          slideType: "native",
          nativeScreenKey: "custom_message",
          nativeConfig: {
            version: 2,
            headline: "Olá",
            blocks: [
              {
                id: "b1",
                type: "text",
                content: "Teste",
                frame: { x: 5, y: 5, w: 40, h: 10, zIndex: 1 },
              },
            ],
          },
          durationSec: 15,
          sortOrder: 0,
          isActive: true,
        },
      ],
    });

    render(
      <App pathname="/apps/tv-dashboard/playlists/test-playlist" getAccessToken={() => "token"} />,
    );

    expect(
      await screen.findByRole("tab", { name: /página inicial/i, timeout: 8000 }),
    ).toBeTruthy();
  });
});
