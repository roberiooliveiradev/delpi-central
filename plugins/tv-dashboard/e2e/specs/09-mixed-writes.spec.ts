import { expect, test, type Page } from "@playwright/test";
import {
  blockFrameFromApi,
  FIXTURE,
  loginAs,
  openEditor,
  readBack,
  resetSlideA,
  selectSlide,
} from "../helpers";

/**
 * Scenario 9 — mixed writes (028, Pendência B).
 *
 * Contrato: enquanto uma PresentationMutation cobre entidades do slide, uma
 * edição AUTOSAVE-ONLY legítima (ex.: texto digitado — `updateBlockTextFields`
 * → `updateBlocks` → autosave PATCH, sem op governada) continua persistindo,
 * mas o PATCH full-config NÃO transporta a projeção mutation-backed pendente:
 * as entidades cobertas serializam o baseline confirmado.
 */

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

/** Edição autosave-only real: dblclick → digita → blur (commitDraft → autosave). */
async function editTextBlock(page: Page, blockId: string, text: string): Promise<void> {
  await page
    .locator('.td-composer__block-wrap[data-block-id="' + blockId + '"]')
    .dblclick();
  const box = page.getByRole("textbox").first();
  await box.waitFor({ state: "visible", timeout: 10_000 });
  await box.fill(text);
  // Blur real: clica no palco fora do editor — commitDraft persiste via autosave.
  await page.mouse.click(20, 20);
}

function patchBlock(
  body: string,
  blockId: string,
): Record<string, unknown> | undefined {
  try {
    const parsed = JSON.parse(body) as {
      nativeConfig?: { blocks?: Array<Record<string, unknown>> };
    };
    return parsed.nativeConfig?.blocks?.find(
      (b) => (b as { id?: string }).id === blockId,
    );
  } catch {
    return undefined;
  }
}

async function blockContentFromApi(
  slideId: string,
  blockId: string,
): Promise<string | undefined> {
  const pl = await readBack("editor");
  const slide = pl.slides.find((s) => s.id === slideId);
  const block = slide?.nativeConfig?.blocks?.find(
    (b) => (b as { id?: string }).id === blockId,
  );
  return (block as { content?: string } | undefined)?.content;
}

const NEW_TEXT = "MIXED_AUTOSAVE_TEXT_028";

test.describe("Scenario 9 — mixed writes: mutation pendente + autosave-only (028)", () => {
  test.beforeEach(async () => {
    await resetSlideA("editor");
  });

  test("B1 — autosave-only persiste; PATCH carrega baseline (não a projeção); rejeição não persiste", async ({
    page,
  }) => {
    test.setTimeout(120_000);
    const patchBodies: string[] = [];
    page.on("request", (r) => {
      if (r.method() === "PATCH" && r.url().includes("playlist")) {
        patchBodies.push(
          JSON.stringify(r.postDataJSON() ?? r.postData()),
        );
      }
    });

    await loginAs(page, "editor");
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);

    // Segura a mutation do slide A na rede até release() — ACK nunca chega antes.
    let release: (() => void) | null = null;
    const gate = new Promise<void>((res) => (release = res));
    const mutPattern =
      "**/slides/" + FIXTURE.slideA + "/presentation-mutations";
    let mutationCount = 0;
    await page.route(mutPattern, async (route) => {
      mutationCount += 1;
      await gate;
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "e2e forced 500 (mixed B1)" }),
      });
    });

    // Projeção mutation-backed: align-left projeta e2e_txt2 de x=40 → x=8.
    await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
    await page
      .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
      .click({ modifiers: ["Shift"] });
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await page.waitForTimeout(800);
    expect(mutationCount).toBeGreaterThanOrEqual(1);

    // Edição autosave-only enquanto a mutation está pendente.
    await editTextBlock(page, "e2e_txt3", NEW_TEXT);

    // Debounce (~400ms) + folga: o PATCH autosave-only deve disparar com a
    // mutation ainda pendente.
    await page.waitForTimeout(2500);
    release!();
    await page.waitForTimeout(2500);
    await page.unroute(mutPattern);

    // ASSERT núcleo: algum PATCH transportou a edição autosave-only…
    const mixedPatch = patchBodies.find((body) => {
      const txt3 = patchBlock(body, "e2e_txt3") as
        | { content?: string }
        | undefined;
      return txt3?.content === NEW_TEXT;
    });
    expect(
      mixedPatch,
      "esperava um PATCH autosave-only com o novo texto de e2e_txt3",
    ).toBeTruthy();
    // …e NENHUM PATCH transportou a projeção pendente (e2e_txt2.x=8).
    for (const body of patchBodies) {
      const txt2 = patchBlock(body, "e2e_txt2") as
        | { frame?: { x?: number } }
        | undefined;
      if (txt2?.frame?.x === undefined) continue;
      expect(
        txt2.frame.x,
        "PATCH de autosave não pode serializar a projeção mutation-backed",
      ).not.toBe(8);
    }

    // Read-back autoritativo: autosave-only persistiu; projeção rejeitada não.
    const apiX = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
    expect(apiX?.x).toBe(40);
    const apiText = await blockContentFromApi(FIXTURE.slideA, "e2e_txt3");
    expect(apiText).toContain(NEW_TEXT);
  });

  test("B2 — mesma mistura com navegação A→B antes do ACK: flush-on-leave também carrega baseline", async ({
    page,
  }) => {
    test.setTimeout(120_000);
    const patchBodies: string[] = [];
    page.on("request", (r) => {
      if (r.method() === "PATCH" && r.url().includes("playlist")) {
        patchBodies.push(
          JSON.stringify(r.postDataJSON() ?? r.postData()),
        );
      }
    });

    await loginAs(page, "editor");
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);

    let release: (() => void) | null = null;
    const gate = new Promise<void>((res) => (release = res));
    const mutPattern =
      "**/slides/" + FIXTURE.slideA + "/presentation-mutations";
    let mutationCount = 0;
    await page.route(mutPattern, async (route) => {
      mutationCount += 1;
      await gate;
      try {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "e2e forced 500 (mixed B2)" }),
        });
      } catch {
        // página pode abortar o fetch na navegação — a rejeição já é o cenário.
      }
    });

    await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
    await page
      .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
      .click({ modifiers: ["Shift"] });
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await page.waitForTimeout(800);
    expect(mutationCount).toBeGreaterThanOrEqual(1);

    await editTextBlock(page, "e2e_txt3", NEW_TEXT);
    await page.waitForTimeout(400); // ainda dentro do debounce

    // Navega antes do ACK: flush-on-leave do slide A + save do texto.
    await selectSlide(page, FIXTURE.slideB);
    await page.waitForTimeout(2000);
    release!();
    await page.waitForTimeout(3000);
    await page.unroute(mutPattern);

    for (const body of patchBodies) {
      const txt2 = patchBlock(body, "e2e_txt2") as
        | { frame?: { x?: number } }
        | undefined;
      if (txt2?.frame?.x === undefined) continue;
      expect(
        txt2.frame.x,
        "flush-on-leave não pode serializar a projeção pendente",
      ).not.toBe(8);
    }

    const apiX = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
    expect(apiX?.x).toBe(40);
    const apiText = await blockContentFromApi(FIXTURE.slideA, "e2e_txt3");
    expect(apiText).toContain(NEW_TEXT);
  });

  test("B4 — ACK confirmado: edição autosave-only e mutation persistem exatamente uma vez", async ({
    page,
  }) => {
    test.setTimeout(120_000);
    let released = false;
    const preAckPatches: string[] = [];
    const postAckPatches: string[] = [];
    page.on("request", (r) => {
      if (r.method() === "PATCH" && r.url().includes("playlist")) {
        const body = JSON.stringify(r.postDataJSON() ?? r.postData());
        (released ? postAckPatches : preAckPatches).push(body);
      }
    });

    await loginAs(page, "editor");
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);

    // Atrasa o ACK além do debounce — autosave-only dispara com a mutation in-flight.
    let release: (() => void) | null = null;
    const gate = new Promise<void>((res) => (release = res));
    const mutPattern =
      "**/slides/" + FIXTURE.slideA + "/presentation-mutations";
    let mutationCount = 0;
    await page.route(mutPattern, async (route) => {
      mutationCount += 1;
      await gate;
      released = true;
      await route.continue();
    });

    await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
    await page
      .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
      .click({ modifiers: ["Shift"] });
    await contextCommand(page, "e2e_txt1", ["Alinhar", "Alinhar à esquerda"]);
    await page.waitForTimeout(800);
    expect(mutationCount).toBe(1);

    await editTextBlock(page, "e2e_txt3", NEW_TEXT);
    await page.waitForTimeout(1500); // PATCH autosave-only com baseline
    release!();
    await page.waitForTimeout(3000);
    await page.unroute(mutPattern);

    // Estado final: projeção confirmada (x=8) + edição autosave-only persistidas.
    const apiX = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
    expect(apiX?.x).toBe(8);
    const apiText = await blockContentFromApi(FIXTURE.slideA, "e2e_txt3");
    expect(apiText).toContain(NEW_TEXT);

    // Antes do ACK nenhum PATCH pode transportar a projeção não confirmada.
    for (const body of preAckPatches) {
      const txt2 = patchBlock(body, "e2e_txt2") as
        | { frame?: { x?: number } }
        | undefined;
      if (txt2?.frame?.x === undefined) continue;
      expect(
        txt2.frame.x,
        "PATCH pré-ACK serializou projeção mutation-backed pendente",
      ).not.toBe(8);
    }
    // Pós-ACK, o único PATCH legítimo seria o delta autosave-only remanescente
    // (com texto). Um PATCH canônico redundante sem delta é write duplicado.
    for (const body of postAckPatches) {
      const txt3 = patchBlock(body, "e2e_txt3") as
        | { content?: string }
        | undefined;
      expect(
        txt3?.content,
        "PATCH pós-ACK sem delta autosave-only = write duplicado do canônico",
      ).toContain(NEW_TEXT);
    }
  });
});
