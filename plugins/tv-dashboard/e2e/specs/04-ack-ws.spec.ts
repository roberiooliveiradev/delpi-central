import { expect, test, type Page } from "@playwright/test";
import {
  blockStyle,
  FIXTURE,
  loginAs,
  openEditor,
  resetSlideA,
  selectSlide,
} from "../helpers";

async function contextCommand(
  page: Page,
  anchorBlockId: string,
  path: string[],
): Promise<void> {
  await page
    .locator('.td-composer__block-wrap[data-block-id="' + anchorBlockId + '"]')
    .click({ button: "right" });
  for (let i = 0; i < path.length; i += 1) {
    const item = page
      .getByRole("menuitem", { name: path[i], exact: true })
      .first();
    if (i < path.length - 1) {
      await item.hover();
    } else {
      await item.click();
    }
  }
}

/** Conta GETs de reload da playlist (read-back completo). */
function countPlaylistLoads(page: Page, bucket: string[]): () => number {
  let n = 0;
  page.on("response", (r) => {
    const u = r.url();
    const tail = u.split("/playlists/")[1] ?? "";
    if (
      r.request().method() === "GET" &&
      u.includes("/apps/tv-dashboard-api/playlists/") &&
      /^[0-9a-f-]{36}([?].*)?$/.test(tail)
    ) {
      n += 1;
      bucket.push(u);
    }
  });
  return () => n;
}

test.describe("Scenario 4 — ACK / WebSocket", () => {
  test.beforeEach(async () => {
    await resetSlideA("editor");
  });

  test("commit próprio não dispara reload redundante; evento externo dispara", async ({
    browser,
  }) => {
    const ctxA = await browser.newContext();
    const ctxB = await browser.newContext();
    const pageA = await ctxA.newPage();
    const pageB = await ctxB.newPage();
    await loginAs(pageA, "editor");
    await loginAs(pageB, "manager");
    await openEditor(pageA);
    await openEditor(pageB);
    await selectSlide(pageA, FIXTURE.slideA);
    await selectSlide(pageB, FIXTURE.slideA);

    const urlsA: string[] = [];
    const urlsB: string[] = [];
    const loadsA = countPlaylistLoads(pageA, urlsA);
    const loadsB = countPlaylistLoads(pageB, urlsB);
    await pageA.waitForTimeout(2000); // baseline: ignora loads iniciais
    const baseA = loadsA();
    const baseB = loadsB();

    // A comanda um z-order — escrita própria.
    const ack = pageA.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(pageA, "e2e_icon", ["Organizar", "Avançar"]);
    await ack;

    // Janela de observação do eco WS.
    await pageA.waitForTimeout(8000);

    // eslint-disable-next-line no-console
    console.log("URLS_A:", JSON.stringify(urlsA), "URLS_B:", JSON.stringify(urlsB));
    // 024: commit próprio incorporado não recarrega a playlist.
    expect(loadsA() - baseA, "A não deve recarregar por eco próprio").toBe(0);
    // Evento externo: B deve recarregar (load autoritativo).
    expect(loadsB() - baseB, "B deve recarregar por evento externo").toBeGreaterThanOrEqual(1);

    // Convergência visual.
    const styleA = await blockStyle(pageA, "e2e_icon");
    await expect
      .poll(() => blockStyle(pageB, "e2e_icon"), { timeout: 25_000 })
      .toBe(styleA);

    await ctxA.close();
    await ctxB.close();
  });
});
