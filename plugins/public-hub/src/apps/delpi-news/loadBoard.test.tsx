/** @vitest-environment node */

import { describe, expect, it } from "vitest";

import type { DelpiNewsDemoEnv } from "./demoMode";
import { DELPI_NEWS_DEMO_TOKEN, DELPI_NEWS_LEGACY_OPEN_TOKEN } from "./demoMode";
import { loadPublicNewsBoard } from "./loadBoard";
import { MOCK_PUBLIC_NEWS_BOARD } from "./mockFeed";

const DEV_ENV: DelpiNewsDemoEnv = { DEV: true };
const PROD_ENV: DelpiNewsDemoEnv = { DEV: false };
const HOMOLOG_ENV: DelpiNewsDemoEnv = { DEV: false, VITE_DELPI_NEWS_DEMO: "1" };

describe("loadPublicNewsBoard", () => {
  it("positive: em DEV o token demo retorna a fixture", async () => {
    const board = await loadPublicNewsBoard(DELPI_NEWS_DEMO_TOKEN, DEV_ENV);
    expect(board).not.toBeNull();
    expect(board?.board_id).toBe(MOCK_PUBLIC_NEWS_BOARD.board_id);
    expect(board?.is_demo).toBe(true);
  });

  it("sibling: homologação com VITE_DELPI_NEWS_DEMO=1 libera a fixture", async () => {
    const board = await loadPublicNewsBoard(DELPI_NEWS_DEMO_TOKEN, HOMOLOG_ENV);
    expect(board?.title).toContain("Demonstração");
    expect(board?.items.length).toBeGreaterThan(0);
  });

  it("negative: em produção sem flag a demonstração fica bloqueada", async () => {
    await expect(loadPublicNewsBoard(DELPI_NEWS_DEMO_TOKEN, PROD_ENV)).resolves.toBeNull();
    await expect(loadPublicNewsBoard(DELPI_NEWS_LEGACY_OPEN_TOKEN, PROD_ENV)).resolves.toBeNull();
  });

  it("negative: token legado aberto nunca carrega o mock", async () => {
    await expect(loadPublicNewsBoard(DELPI_NEWS_LEGACY_OPEN_TOKEN, DEV_ENV)).resolves.toBeNull();
  });

  it("negative: token desconhecido retorna null", async () => {
    await expect(loadPublicNewsBoard("token-inexistente", DEV_ENV)).resolves.toBeNull();
  });
});
