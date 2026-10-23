import { expect, test } from "@playwright/test";
import { apiToken, FIXTURE, loginAs, openEditor, selectSlide } from "../helpers";
import { request } from "@playwright/test";

test.describe("Scenario 7 — perfil somente leitura", () => {
  test("viewer: visualização autorizada, escrita rejeitada pelo backend", async ({
    page,
  }) => {
    await loginAs(page, "viewer");
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);

    // Palco renderiza (leitura permitida).
    await expect(
      page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]'),
    ).toBeVisible();

    // Backend rejeita escrita direta — ocultar botão não é prova de segurança.
    const tok = await apiToken("viewer");
    const ctx = await request.newContext({
      baseURL: process.env.TV_E2E_BASE_URL ?? "http://localhost",
    });
    const res = await ctx.post(
      "/apps/tv-dashboard-api/playlists/" +
        FIXTURE.playlistId +
        "/slides/" +
        FIXTURE.slideA +
        "/presentation-mutations",
      {
        headers: { Authorization: "Bearer " + tok },
        data: {
          ops: [
            {
              op: "upsert_block",
              block: {
                id: "e2e_txt1",
                type: "text",
                frame: { x: 0, y: 0, w: 10, h: 10 },
              },
            },
          ],
        },
      },
    );
    await ctx.dispose();
    expect([401, 403]).toContain(res.status());
  });
});
