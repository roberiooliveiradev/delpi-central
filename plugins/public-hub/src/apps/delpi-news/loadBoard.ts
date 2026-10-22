import { MOCK_PUBLIC_NEWS_BOARD } from "./mockFeed";
import type { PublicNewsBoard } from "./types";

/** Token estático da prova visual: /p/delpi-news/board/aberto */
export const DELPI_NEWS_PUBLIC_TOKEN = "aberto";

/**
 * Carrega o board público. Etapa 1: somente fixture.
 * Etapa futura: GET /apps/delpi-news-api/public/boards/{token}.
 */
export async function loadPublicNewsBoard(token: string): Promise<PublicNewsBoard | null> {
  if (token !== DELPI_NEWS_PUBLIC_TOKEN) {
    return null;
  }
  return MOCK_PUBLIC_NEWS_BOARD;
}
