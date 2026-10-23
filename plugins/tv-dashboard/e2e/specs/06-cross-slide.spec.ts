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

async function leftPct(page: Page, blockId: string): Promise<number> {
  const style = await blockStyle(page, blockId);
  const m = /left:\s*([\d.]+)%/.exec(style);
  return m ? Number(m[1]) : -1;
}

test.describe("Scenario 6 — navegação entre slides durante falha (025-R2)", () => {
  test.beforeEach(async () => {
    await resetSlideA("editor");
  });

  test("mutação de A pendente + navegação para B: identidade preservada, B intacto, A autoritativo", async ({
    page,
  }) => {
    test.setTimeout(120_000);
    const writes: string[] = [];
    const patchBodies: string[] = [];
    page.on('request', (r) => {
      if (r.method() !== 'GET' && r.url().includes('playlist')) {
        writes.push(r.method() + ' ' + r.url());
        if (r.method() === 'PATCH') patchBodies.push(JSON.stringify(r.postDataJSON() ?? r.postData()));
      }
    });
    const consoleErrors: string[] = [];
    page.on("pageerror", (e) => consoleErrors.push(String(e)));

    await loginAs(page, "editor");
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);
    const persistedLeft = await leftPct(page, "e2e_txt2");

    // Gate: segura a 1ª mutação do slide A na camada de rede e conta todas.
    let release: (() => void) | null = null;
    const gate = new Promise<void>((res) => (release = res));
    const slideAPattern = "**/slides/" + FIXTURE.slideA + "/presentation-mutations";
    let requestCount = 0;
    let clientAborted = false;
    let fulfilled = false;
    await page.route(slideAPattern, async (route) => {
      requestCount += 1;
      if (requestCount === 1) {
        await gate;
        try {
          await route.fulfill({
            status: 500,
            contentType: "application/json",
            body: JSON.stringify({ detail: "e2e forced 500" }),
          });
          fulfilled = true;
        } catch {
          clientAborted = true; // página abortou o fetch durante a navegação
        }
        return;
      }
      await route.continue();
    });

    // Align local-first em A (projeção imediata esperada).
    await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
    await page
      .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
      .click({ modifiers: ["Shift"] });
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await page.waitForTimeout(800);
    expect(requestCount).toBeGreaterThanOrEqual(1);

    // Navega para B ANTES da resposta de A.
    await selectSlide(page, FIXTURE.slideB);
    await page.waitForTimeout(1500);
    release!();
    await page.waitForTimeout(3000);
    await page.unroute(slideAPattern);

    // B permanece renderizado e estável — nunca invalidado pelo resultado de A.
    await expect(page.locator("[data-block-id]").first()).toBeVisible();
    await page.waitForTimeout(2000);
    await expect(page.locator("[data-block-id]").first()).toBeVisible();

    // Estado autoritativo real de A segundo o backend.
    const apiAfter = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");

    // INVARIANTE (025/026): uma mutação rejeitada (HTTP 500) NÃO pode persistir.
    // A projeção otimista de A não pode vazar para o estado autoritativo.
    // DEFEITO CONHECIDO 026-F1: o autosave comunicado (PATCH updateSlide com o
    // nativeConfig completo) serializa a projeção antes do ACK — sob navegação,
    // o flush antecipado grava a geometria projetada mesmo com a mutação
    // rejeitada. Esta asserção FALHA enquanto o vazamento existir.
    expect(
      apiAfter?.x,
      "mutação rejeitada não pode persistir via autosave",
    ).toBeCloseTo(persistedLeft, 0);

    // Voltando para A: o que o DOM mostra deve convergir para o estado
    // autoritativo (sem projeção órfã divergente do servidor).
    await selectSlide(page, FIXTURE.slideA);
    await expect
      .poll(() => leftPct(page, "e2e_txt2"), { timeout: 45_000 })
      .toBeCloseTo(apiAfter?.x ?? persistedLeft, 0);

    // Sem erro JS não tratado no fluxo.
    expect(
      consoleErrors.filter((e) => !/favicon|dev/i.test(e)),
      "pageerrors",
    ).toEqual([]);

    // Telemetria da observação (documenta comportamento real da navegação).
    // eslint-disable-next-line no-console
    console.log(
      JSON.stringify({ requestCount, clientAborted, fulfilled, apiX: apiAfter?.x, writes, patchBodies: patchBodies.map((b)=>b.slice(0,1200)), patchX: patchBodies.map((b) => { const m = /e2e_txt2[^}]*?frame[^}]*?x.:([d.]+)/.exec(b); return m?.[1]; }) }),
    );
  });

  test("caso irmão sem navegação: 500 tardio (>400ms) vaza projeção pelo autosave debounced", async ({
    page,
  }) => {
    test.setTimeout(120_000);
    await loginAs(page, "editor");
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);
    const persistedLeft = await leftPct(page, "e2e_txt2");

    // 500 atrasado 1200ms — o PATCH de autosave (debounce ~400ms) dispara antes.
    const slideAPattern = "**/slides/" + FIXTURE.slideA + "/presentation-mutations";
    await page.route(slideAPattern, async (route) => {
      await page.waitForTimeout(1200);
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "e2e delayed 500" }),
      });
    });

    await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
    await page
      .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
      .click({ modifiers: ["Shift"] });
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);

    // Espera a falha + recuperação assentarem.
    await page.waitForTimeout(15_000);
    await page.unroute(slideAPattern);

    const apiAfter = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
    // Mesma invariante: mutação rejeitada não pode persistir via autosave.
    expect(
      apiAfter?.x,
      "mutação rejeitada não pode persistir via autosave (sem navegação)",
    ).toBeCloseTo(persistedLeft, 0);
  });
});
