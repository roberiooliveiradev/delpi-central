import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PlaylistHistoryEntry } from "../../api/tvDashboardApi";
import type { DeckEditorHistoryContextValue } from "../../context/deckEditorHistoryContext";
import { ConfirmDialogProvider } from "../../context/ConfirmDialogProvider";
import { DeckEditorHistoryProvider } from "../../context/deckEditorHistoryContext";
import { DeckRevisionHistoryPanel } from "./DeckRevisionHistoryPanel";

const apiMocks = vi.hoisted(() => ({
  getPlaylistHistorySnapshot: vi.fn(),
}));

vi.mock("../../api/tvDashboardApi", async (importOriginal) => {
  const original = await importOriginal<typeof import("../../api/tvDashboardApi")>();
  return { ...original, getPlaylistHistorySnapshot: apiMocks.getPlaylistHistorySnapshot };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("DeckRevisionHistoryPanel", () => {
  it("usa Timeline canônica e permite detalhar e restaurar uma revisão", async () => {
    const loadHistory = vi.fn().mockResolvedValue(null);
    const restoreRevision = vi.fn().mockResolvedValue(true);
    const entry: PlaylistHistoryEntry = {
      snapshotId: "snap-4",
      revision: 4,
      createdAt: "2026-07-16T12:00:00Z",
      authorName: "Ana Souza",
      authorEmail: "ana@delpi.com.br",
      preview: { playlistName: "TV Fábrica", slideTitles: ["OEE"] },
      change: {
        available: true,
        comparedToRevision: 3,
        playlistFields: ["name"],
        slides: {
          added: [{ id: "slide-1", title: "OEE" }],
          updated: [{ id: "slide-2", title: "OTD", fields: ["nativeConfig"] }],
        },
        totals: { added: 1, removed: 0, updated: 1 },
      },
    };
    apiMocks.getPlaylistHistorySnapshot.mockResolvedValue({
      ...entry,
      snapshot: {
        playlist: { name: "TV Fábrica" },
        slides: [{ id: "slide-1", playlistId: "pl-1", sortOrder: 0, slideType: "native", title: "OEE", isActive: true }],
      },
    });
    const value: DeckEditorHistoryContextValue = {
      playlistId: "pl-1",
      recordBeforeChange: vi.fn(),
      confirmChange: vi.fn().mockResolvedValue(undefined),
      cancelChange: vi.fn(),
      undo: vi.fn(),
      redo: vi.fn(),
      canUndo: false,
      canRedo: false,
      historyEpoch: 0,
      historyPage: {
        items: [entry],
        page: 1,
        pageSize: 10,
        total: 1,
        totalPages: 1,
        hasNext: false,
        currentRevision: 5,
      },
      loading: false,
      restoring: false,
      error: null,
      loadHistory,
      restoreRevision,
      setLiveComunicadoConfig: vi.fn(),
    };

    render(
      <ConfirmDialogProvider>
        <DeckEditorHistoryProvider value={value}>
          <DeckRevisionHistoryPanel open playlistId="pl-1" onClose={vi.fn()} />
        </DeckEditorHistoryProvider>
      </ConfirmDialogProvider>,
    );

    expect(document.querySelector(".delpi-ui-timeline")).toBeTruthy();
    expect(document.querySelector(".td-history__list")).toBeNull();
    expect(screen.getByText("Ana Souza · ana@delpi.com.br")).toBeTruthy();
    expect(
      screen.getByText(
        /1 campo alterado: nome; 1 tela adicionada: OEE; 1 tela editada: OTD \(conteúdo\)/,
      ),
    ).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Ver detalhes da revisão 4" }));
    expect(await screen.findByText("1 tela(s)")).toBeTruthy();
    expect(apiMocks.getPlaylistHistorySnapshot).toHaveBeenCalledWith("pl-1", "snap-4");

    fireEvent.click(screen.getByRole("button", { name: "Restaurar" }));
    const restoreButtons = await screen.findAllByRole("button", { name: "Restaurar" });
    fireEvent.click(restoreButtons.at(-1)!);
    await waitFor(() => expect(restoreRevision).toHaveBeenCalledWith("snap-4", 4));
  });
});
