async function leftPct(page: Page, blockId: string): Promise<number> {
  const style = await blockStyle(page, blockId);
  const m = /left:s*([d.]+)%/.exec(style);
  return m ? Number(m[1]) : -1;
}
import { expect, test, type Page, type Route } from "@playwright/test";
import {
  blockFrameFromApi,
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

async function runAlign(
  page: Page,
  failMode: "abort" | number,
): Promise<void> {
  await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
  await page
    .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
    .click({ modifiers: ["Shift"] });
  await page
    .locator('.td-composer__block-wrap[data-block-id="e2e_txt3"]')
    .click({ modifiers: ["Shift"] });
  if (failMode === "abort") {
    await page.route("**/presentation-mutations", (r: Route) => r.abort());
  } else {
    await page.route("**/presentation-mutations", (r: Route) =>
      r.fulfill({ status: failMode, body: '{"error":"e2e"}' }),
    );
  }
  await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
}

test.describe("Scenario 5 — falhas e recuperação", () => {
  test.beforeEach(async () => {
    await resetSlideA("editor");
  });

  for (const [name, mode] of [
    ["HTTP 500", 500],
    ["HTTP 422", 422],
    ["falha de rede", "abort"],
  ] as Array<[string, "abort" | number]>) {
    test(`${name}: projeção não permanece falsa — recuperação autoritativa`, async ({
      page,
    }) => {
      await loginAs(page, "editor");
      await openEditor(page);
      await selectSlide(page, FIXTURE.slideA);
      const persistedLeft = await leftPct(page, "e2e_txt2");

      await runAlign(page, mode as "abort" | number);

      // Projeção local deve ser revertida pelo read-back autoritativo.
      await expect
        .poll(() => leftPct(page, "e2e_txt2"), { timeout: 45_000 })
        .toBeCloseTo(persistedLeft, 0);

      // Backend nunca persistiu a projeção.
      const f2 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
      expect(f2?.x).toBeCloseTo(40, 0);

      await page.unroute("**/presentation-mutations");

      // Editor continua utilizável: nova escrita confirma.
      await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
      await page
        .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
        .click({ modifiers: ["Shift"] });
      const ack = page.waitForResponse(
        (r) => r.url().includes("presentation-mutations"),
        { timeout: 15_000 },
      );
      await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
      const resp = await ack;
      expect(resp.ok()).toBeTruthy();
    });
  }

  test("ACK perdido após commit — read-back decide (sem rollback cego)", async ({
    page,
  }) => {
    await loginAs(page, "editor");
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);
    const persisted = await blockStyle(page, "e2e_txt2");

    // Aborta a RESPOSTA: request chega ao server (pode commitar) e o ACK se perde.
    await page.route("**/presentation-mutations", async (route) => {
      const resp = await route.fetch();
      void resp; // commit realizado no server
      await route.abort();
    });
    await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
    await page
      .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
      .click({ modifiers: ["Shift"] });
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await page.waitForTimeout(3000);
    await page.unroute("**/presentation-mutations");

    // Estado autoritativo: o server recebeu e persistiu.
    const f2 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
    const f1 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt1");
    const committed = f2?.x !== undefined && f1?.x !== undefined && Math.abs(f2.x - f1.x) < 0.5;

    // Editor converge para o estado AUTORITATIVO (qualquer que seja) — não rollback cego.
    const authoritative = committed ? f2!.x : 40;
    await expect
      .poll(async () => {
        const style = await blockStyle(page, "e2e_txt2");
        const m = /left:\s*([\d.]+)%/.exec(style);
        return m ? Number(m[1]) : -1;
      }, { timeout: 45_000 })
      .toBeCloseTo(authoritative, 0);
    void persisted;
  });
});
