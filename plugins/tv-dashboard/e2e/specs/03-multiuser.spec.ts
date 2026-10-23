import { expect, test, type Page } from "@playwright/test";
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

const blk = (page: Page, id: string) =>
  page.locator('.td-composer__block-wrap[data-block-id="' + id + '"]');

async function waitStyle(
  page: Page,
  blockId: string,
  expected: string,
  timeout = 20_000,
): Promise<void> {
  await expect.poll(() => blockStyle(page, blockId), { timeout }).toBe(expected);
}

test.describe("Scenario 3 — dois usuários editando", () => {
  test.beforeEach(async () => {
    await resetSlideA("editor");
  });

  test("A: componentes diferentes — convergência sem lost update", async ({
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

    // A: z-order em e2e_txt3; B: align em e2e_txt1+txt2 — blocos disjuntos.
    const ackA = pageA.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(pageA, "e2e_txt3", ["Organizar", "Trazer para a frente"]);
    await ackA;

    await blk(pageB, "e2e_txt1").click();
    await blk(pageB, "e2e_txt2").click({ modifiers: ["Shift"] });
    const ackB = pageB.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(pageB, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await ackB;

    // Convergência: ambos os editors devem refletir o mesmo estado final.
    const styleB_txt2 = await blockStyle(pageB, "e2e_txt2");
    await waitStyle(pageA, "e2e_txt2", styleB_txt2);
    const styleB_txt3 = await blockStyle(pageB, "e2e_txt3");
    await waitStyle(pageA, "e2e_txt3", styleB_txt3);

    // Read-back autoritativo confirma os dois efeitos.
    const f2 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
    const f1 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt1");
    expect(f2?.x).toBeCloseTo(f1!.x, 1);

    await ctxA.close();
    await ctxB.close();
  });

  test("B: mesmo componente — 409 resolve server-wins", async ({ browser }) => {
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

    // Segura a mutação de B até o ACK de A (revisão de B fica stale → 409).
    let releaseB: (() => void) | null = null;
    const gate = new Promise<void>((res) => (releaseB = res));
    await pageB.route("**/presentation-mutations", async (route) => {
      await gate;
      await route.continue();
    });

    // A confirma primeiro.
    await blk(pageA, "e2e_txt1").click();
    await blk(pageA, "e2e_txt2").click({ modifiers: ["Shift"] });
    const ackA = pageA.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(pageA, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await ackA;
    const styleA = await blockStyle(pageA, "e2e_txt2");

    // B escreve sobre revisão pré-A → 409 → server-wins.
    await blk(pageB, "e2e_txt1").click();
    await blk(pageB, "e2e_txt2").click({ modifiers: ["Shift"] });
    await contextCommand(pageB, "e2e_txt1", ["Alinhar", "Alinhar à direita"]);
    releaseB!();
    await pageB.unroute("**/presentation-mutations");

    // Server-wins: B deve convergir para o estado persistido por A.
    await waitStyle(pageB, "e2e_txt2", styleA, 30_000);
    const f2 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
    const f1 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt1");
    expect(f2?.x).toBeCloseTo(f1!.x, 1);

    await ctxA.close();
    await ctxB.close();
  });

  test("C: Undo após baseline remota não sobrescreve escrita externa (023)", async ({
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

    // B cria histórico local (z-order em e2e_icon — isolado do alvo de A).
    const ackB = pageB.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(pageB, "e2e_icon", ["Organizar", "Avançar"]);
    await ackB;

    // A confirma alteração em e2e_txt1+txt2 — baseline estrangeira para B.
    await blk(pageA, "e2e_txt1").click();
    await blk(pageA, "e2e_txt2").click({ modifiers: ["Shift"] });
    const ackA = pageA.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(pageA, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await ackA;

    // B recebe a atualização via WS.
    const styleA_txt2 = await blockStyle(pageA, "e2e_txt2");
    await waitStyle(pageB, "e2e_txt2", styleA_txt2);

    // B tenta Undo: histórico local invalidado pela baseline remota.
    // Resultado exigido: a escrita de A em txt2 NÃO é revertida por B.
    const undo = pageB.locator('button[aria-label="Desfazer"]');
    if (await undo.isEnabled().catch(() => false)) {
      await undo.click();
      // Se um Undo local ocorrer, deve afetar somente a ação de B (e2e_icon).
      await pageB.waitForTimeout(2000);
    }
    await expect
      .poll(() => blockStyle(pageB, "e2e_txt2"), { timeout: 15_000 })
      .toBe(styleA_txt2);
    const f2 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
    expect(f2?.x).toBeCloseTo(
      (await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt1"))!.x,
      1,
    );

    await ctxA.close();
    await ctxB.close();
  });

  test("F: reconexão — estado autoritativo após offline", async ({ browser }) => {
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

    // A fica offline; B confirma uma alteração.
    await ctxA.setOffline(true);
    await blk(pageB, "e2e_txt1").click();
    await blk(pageB, "e2e_txt2").click({ modifiers: ["Shift"] });
    const ackB = pageB.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(pageB, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await ackB;
    const styleB = await blockStyle(pageB, "e2e_txt2");

    // A volta online e sincroniza para o estado autoritativo.
    await ctxA.setOffline(false);
    await waitStyle(pageA, "e2e_txt2", styleB, 45_000);

    await ctxA.close();
    await ctxB.close();
  });
});
