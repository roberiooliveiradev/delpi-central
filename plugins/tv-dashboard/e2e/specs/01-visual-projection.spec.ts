import { expect, test, type Page } from "@playwright/test";
import {
  blockFrameFromApi,
  resetSlideA,
  blockStyle,
  FIXTURE,
  loginAs,
  measureCommand,
  openEditor,
  selectSlide,
  type CommandTiming,
} from "../helpers";

const RESULTS: Array<{ command: string } & CommandTiming> = [];

/**
 * Comando via menu de contexto do palco: botão direito no bloco
 * → item de menu → (submenu) → comando real do editor.
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

async function selectThree(page: Page): Promise<void> {
  await page.locator('.td-composer__block-wrap[data-block-id="e2e_txt1"]').click();
  await page
    .locator('.td-composer__block-wrap[data-block-id="e2e_txt2"]')
    .click({ modifiers: ["Shift"] });
  await page
    .locator('.td-composer__block-wrap[data-block-id="e2e_txt3"]')
    .click({ modifiers: ["Shift"] });
}

test.describe("Scenario 1 — resposta visual imediata", () => {
  test.beforeEach(async ({ page }) => {
    await resetSlideA("editor");
    await loginAs(page, "editor");
    await openEditor(page);
    await selectSlide(page, FIXTURE.slideA);
  });

  test.afterAll(() => {
    // eslint-disable-next-line no-console
    console.log(JSON.stringify({ scenario: 1, results: RESULTS }, null, 2));
  });

  const cases: Array<{
    name: string;
    select: (p: Page) => Promise<void>;
    anchor: string;
    watch: string[];
    path: string[];
    expectPersisted: (p: Page) => Promise<void>;
  }> = [
    {
      name: "align-left",
      select: selectThree,
      anchor: "e2e_txt1",
      watch: ["e2e_txt2", "e2e_txt3"],
      path: ["Alinhar", "Alinhar à esquerda"],
      expectPersisted: async () => {
        const f1 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt1");
        const f2 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
        const f3 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt3");
        expect(f2?.x).toBeCloseTo(f1!.x, 1);
        expect(f3?.x).toBeCloseTo(f1!.x, 1);
      },
    },
    {
      name: "align-center-v",
      select: selectThree,
      anchor: "e2e_txt1",
      watch: ["e2e_txt1", "e2e_txt2", "e2e_txt3"],
      path: ["Alinhar", "Alinhar ao meio"],
      expectPersisted: async () => {
        const f1 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt1");
        const f2 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
        expect(f2?.y).toBeCloseTo(f1!.y, 1);
      },
    },
    {
      name: "distribute-h",
      select: selectThree,
      anchor: "e2e_txt1",
      watch: ["e2e_txt2"],
      path: ["Alinhar", "Distribuir horizontalmente"],
      expectPersisted: async () => {
        const xs = await Promise.all(
          ["e2e_txt1", "e2e_txt2", "e2e_txt3"].map((id) =>
            blockFrameFromApi("editor", FIXTURE.slideA, id),
          ),
        );
        const sorted = xs.map((f) => f!.x).sort((a, b) => a - b);
        expect(sorted[1]! - sorted[0]!).toBeCloseTo(sorted[2]! - sorted[1]!, 1);
      },
    },
    {
      name: "distribute-v",
      select: selectThree,
      anchor: "e2e_txt1",
      watch: ["e2e_txt2"],
      path: ["Alinhar", "Distribuir verticalmente"],
      expectPersisted: async () => {
        const ys = await Promise.all(
          ["e2e_txt1", "e2e_txt2", "e2e_txt3"].map((id) =>
            blockFrameFromApi("editor", FIXTURE.slideA, id),
          ),
        );
        const sorted = ys.map((f) => f!.y).sort((a, b) => a - b);
        expect(sorted[1]! - sorted[0]!).toBeCloseTo(sorted[2]! - sorted[1]!, 1);
      },
    },
    {
      name: "bring-to-front",
      select: async (p) => p.locator('.td-composer__block-wrap[data-block-id="e2e_txt3"]').click(),
      anchor: "e2e_txt3",
      watch: ["e2e_txt3"],
      path: ["Organizar", "Trazer para a frente"],
      expectPersisted: async () => {},
    },
    {
      name: "send-to-back",
      select: async (p) => p.locator('.td-composer__block-wrap[data-block-id="e2e_txt3"]').click(),
      anchor: "e2e_txt3",
      watch: ["e2e_txt3"],
      path: ["Organizar", "Enviar para trás"],
      expectPersisted: async () => {},
    },
    {
      name: "bring-forward",
      select: async (p) => p.locator('.td-composer__block-wrap[data-block-id="e2e_txt3"]').click(),
      anchor: "e2e_txt3",
      watch: ["e2e_txt3"],
      path: ["Organizar", "Avançar"],
      expectPersisted: async () => {},
    },
    {
      name: "send-backward",
      select: async (p) => p.locator('.td-composer__block-wrap[data-block-id="e2e_txt3"]').click(),
      anchor: "e2e_txt3",
      watch: ["e2e_txt3"],
      path: ["Organizar", "Recuar"],
      expectPersisted: async () => {},
    },
    {
      name: "align-center-h",
      select: selectThree,
      anchor: "e2e_txt1",
      watch: ["e2e_txt2", "e2e_txt3"],
      path: ["Alinhar", "Centralizar"],
      expectPersisted: async () => {
        const f1 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt1");
        const f2 = await blockFrameFromApi("editor", FIXTURE.slideA, "e2e_txt2");
        const c1 = f1!.x + f1!.w / 2;
        const c2 = f2!.x + f2!.w / 2;
        expect(c2).toBeCloseTo(c1, 1);
      },
    },
  ];

  for (const c of cases) {
    test(`projeção imediata + persistência: ${c.name}`, async ({ page }) => {
      await c.select(page);
      const timing = await measureCommand(page, c.watch, () =>
        contextCommand(page, c.anchor, c.path),
      );
      RESULTS.push({ command: c.name, ...timing });

      // Projeção imediata: primeiro frame visual antes do ACK.
      expect(timing.clickToFirstVisualMs, `${c.name}: first visual`).not.toBeNull();
      expect(timing.clickToAckMs, `${c.name}: ack`).not.toBeNull();
      expect(timing.clickToFirstVisualMs!).toBeLessThanOrEqual(
        timing.clickToAckMs! + 1,
      );

      // ACK não pode corrigir a projeção (salto pós-read-back).
      expect(timing.visualCorrections, `${c.name}: visual jump`).toBe(0);

      await c.expectPersisted(page);
    });
  }
});
