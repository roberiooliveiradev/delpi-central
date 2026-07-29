import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { clearPreviewPayloadCache } from "../utils/previewPayloadCache";

vi.mock("../api/tvDashboardApi", () => ({
  getPreviewPayload: () => new Promise(() => undefined),
}));

vi.mock("../presentation/PresentationPreview", () => ({
  PresentationPreview: () => null,
}));

describe("PlaylistPreviewPage loading", () => {
  afterEach(() => {
    cleanup();
    clearPreviewPayloadCache();
  });

  it("usa ScreenLoading da apresentação enquanto o payload não chega", async () => {
    const { PlaylistPreviewPage } = await import("./PlaylistPreviewPage");
    render(<PlaylistPreviewPage playlistId="pl-loading" onBack={() => undefined} />);

    const splash = screen.getByRole("status", { name: "Carregando" });
    expect(splash.className).toContain("delpi-ui-screen-loading");
    expect(splash.className).toContain("delpi-ui-screen-loading--fullscreen");
    expect(splash.className).toContain("delpi-ui-screen-loading--dark");
    expect(screen.queryByText("Carregando preview…")).toBeNull();
  });
});
