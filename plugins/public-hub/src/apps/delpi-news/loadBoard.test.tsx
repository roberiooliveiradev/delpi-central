/** @vitest-environment node */

import { describe, expect, it } from "vitest";

import { DELPI_NEWS_PUBLIC_TOKEN, loadPublicNewsBoard } from "./loadBoard";
import { MOCK_PUBLIC_NEWS_BOARD } from "./mockFeed";

describe("loadPublicNewsBoard", () => {
  it("positive: token aberto retorna o board fixture com itens publicados", async () => {
    const board = await loadPublicNewsBoard(DELPI_NEWS_PUBLIC_TOKEN);
    expect(board).not.toBeNull();
    expect(board?.board_id).toBe(MOCK_PUBLIC_NEWS_BOARD.board_id);
    expect(board?.items.length).toBeGreaterThan(0);
    expect(board?.items.every((item) => item.title && item.source_name)).toBe(true);
  });

  it("sibling: shape público contém campos do contrato PublicNewsBoard", async () => {
    const board = await loadPublicNewsBoard("aberto");
    expect(board).toMatchObject({
      title: expect.any(String),
      rotation_interval_sec: expect.any(Number),
      items: expect.arrayContaining([
        expect.objectContaining({
          id: expect.any(String),
          title: expect.any(String),
          source_name: expect.any(String),
          is_featured: expect.any(Boolean),
        }),
      ]),
    });
  });

  it("negative: token desconhecido retorna null (404 do shell)", async () => {
    await expect(loadPublicNewsBoard("token-inexistente")).resolves.toBeNull();
  });
});
