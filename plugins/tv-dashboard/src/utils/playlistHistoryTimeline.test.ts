import { describe, expect, it } from "vitest";

import type { PlaylistHistoryEntry } from "../api/tvDashboardApi";
import {
  playlistHistoryAuthor,
  summarizePlaylistHistoryChange,
} from "./playlistHistoryTimeline";

const BASE_ENTRY: PlaylistHistoryEntry = {
  snapshotId: "snap-8",
  revision: 8,
  createdAt: "2026-07-16T12:00:00Z",
};

describe("playlistHistoryTimeline", () => {
  it("resume autor e mudanças entregues pelo contrato novo", () => {
    const item: PlaylistHistoryEntry = {
      ...BASE_ENTRY,
      authorName: "  Ana Souza ",
      authorEmail: " ana@delpi.com.br ",
      change: {
        available: true,
        comparedToRevision: 7,
        playlistFields: ["name", "transitionStyle"],
        slides: {
          added: [{ id: "s-1", title: "Produção" }],
          removed: [{ id: "s-2", title: "Estoque" }],
          updated: [{ id: "s-3", title: "Qualidade", fields: ["title", "nativeConfig"] }],
          reordered: true,
        },
        totals: {
          added: 1,
          removed: 1,
          updated: 1,
        },
      },
    };

    expect(playlistHistoryAuthor(item)).toEqual({
      name: "Ana Souza",
      email: "ana@delpi.com.br",
    });
    expect(summarizePlaylistHistoryChange(item)).toBe(
      "2 campos alterados: nome e transição; 1 tela adicionada: Produção; 1 tela removida: Estoque; 1 tela editada: Qualidade (título e conteúdo); ordem das telas alterada Alteração resultante na revisão 7.",
    );
  });

  it("mantém fallback legível para snapshots antigos", () => {
    const item: PlaylistHistoryEntry = {
      ...BASE_ENTRY,
      authorId: "usuario-legado",
      reason: "slide_updated",
      preview: { playlistName: "TV Fábrica", slideTitles: ["OEE", "OTD"] },
    };

    expect(playlistHistoryAuthor(item)).toEqual({ name: "usuario-legado", email: null });
    expect(summarizePlaylistHistoryChange(item)).toBe(
      "slide updated · TV Fábrica · OEE, OTD",
    );
  });
});
