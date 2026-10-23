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

async function selectThree(page: Page): Promise<void> {
  await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
  await page
    .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
    .click({ modifiers: ["Shift"] });
  await page
    .locator('.td-composer__block-wrap[data-block-id="e2e_txt3"]')
    .click({ modifiers: ["Shift"] });
}

const undoBtn = (page: Page) => page.locator('button[aria-label="Desfazer"]');
const redoBtn = (page: Page) => page.locator('button[aria-label="Refazer"]');

async function waitStyle(
  page: Page,
  blockId: string,
  expected: string,
): Promise<void> {
  await expect
    .poll(() => blockStyle(page, blockId), { timeout: 15_000 })
    .toBe(expected);
}

test.describe("Scenario 2 — Undo/Redo", () => {
  test.beforeEach(async ({ page }) => {
    await resetSlideA("editor");
    await loginAs(page, "editor");
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);
  });

  test("uma ação lógica = um Undo (ACK normalizado não cria entrada extra)", async ({
    page,
  }) => {
    await selectThree(page);
    const before = await blockStyle(page, "e2e_txt2");
    const ack = page.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await ack;

    // ACK aplicado — um único Undo deve restaurar a posição original.
    await expect(undoBtn(page)).toBeEnabled({ timeout: 10_000 });
    await undoBtn(page).click();
    await waitStyle(page, "e2e_txt2", before);

    // Read-back autoritativo deve refletir o undo persistido.
    await expect
      .poll(
        async () => {
          const f = await blockFrameFromApi(
            "editor",
            FIXTURE.slideA,
            "e2e_txt2",
          );
          return f?.x;
        },
        { timeout: 20_000 },
      )
      .toBeCloseTo(40, 0);
  });

  test("redo reaplica a projeção", async ({ page }) => {
    await selectThree(page);
    const aligned = page.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await aligned;
    const styleAligned = await blockStyle(page, "e2e_txt2");
    const styleBefore = styleAligned === (await blockStyle(page, "e2e_txt2"))
      ? null
      : await blockStyle(page, "e2e_txt2");

    await undoBtn(page).click();
    // Undo aplicado: style volta ao pré-align (diferente do alinhado).
    await expect
      .poll(() => blockStyle(page, "e2e_txt2"), { timeout: 15_000 })
      .not.toBe(styleAligned);

    await expect(redoBtn(page)).toBeEnabled({ timeout: 10_000 });
    await redoBtn(page).click();
    await waitStyle(page, "e2e_txt2", styleAligned);
    void styleBefore;
  });

  test("duas operações consecutivas = dois Undos na ordem inversa", async ({
    page,
  }) => {
    await selectThree(page);
    const before = await blockStyle(page, "e2e_txt2");

    let ack = page.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await ack;
    const afterAlign = await blockStyle(page, "e2e_txt2");

    // Segunda op em bloco único (z-order) — não depende de re-seleção sobreposta.
    const txt3Before = await blockStyle(page, "e2e_txt3");
    ack = page.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(page, "e2e_txt3", ["Organizar", "Avançar"]);
    await ack;
    const txt3Fwd = await blockStyle(page, "e2e_txt3");
    expect(txt3Fwd).not.toBe(txt3Before);

    // Undo 1: reverte o z-order (txt3 volta).
    await undoBtn(page).click();
    await waitStyle(page, "e2e_txt3", txt3Before);
    // txt2 (align) ainda vale.
    expect(await blockStyle(page, "e2e_txt2")).toBe(afterAlign);

    // Undo 2: reverte o align (txt2 volta ao original).
    await undoBtn(page).click();
    await waitStyle(page, "e2e_txt2", before);
  });

  test("undo antes do ACK chegar não perde a reversão", async ({ page }) => {
    await selectThree(page);
    const before = await blockStyle(page, "e2e_txt2");
    const ack = page.waitForResponse(
      (r) => r.url().includes("presentation-mutations"),
      { timeout: 15_000 },
    );
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    // Undo imediato — sem esperar o ACK da mutação.
    await page.keyboard.press("Control+z");
    await waitStyle(page, "e2e_txt2", before);
    await ack.catch(() => null);
    // Estado final autoritativo: posição original.
    await expect
      .poll(
        async () =>
          (await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2"))?.x,
        { timeout: 20_000 },
      )
      .toBeCloseTo(40, 0);
  });
});
