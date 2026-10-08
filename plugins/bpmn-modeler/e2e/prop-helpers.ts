/**
 * WAVE E — helpers de properties panel.
 *
 * Seletores da surface real do vendor (`data-entry-id`/`data-group-id`)
 * — mesma convenção dos specs CE-EVT/IDG. Toda prova passa por read-back
 * autoritativo (fetchWorkingCopyXml) + reload; o DOM do painel só prova
 * interação, nunca persistência.
 */
import { expect, type Page } from "@playwright/test";
import { fetchWorkingCopyXml } from "./ce-helpers";
import type { Actor } from "./helpers";

export const PANEL = "#bpmn-properties-panel .bio-properties-panel";

/**
 * Aguarda o autosave persistir e o read-back autoritativo conter
 * (ou não conter) `pattern`. Sem isto, fetch imediato após o debounce
 * do vendor corre na frente do ciclo dirty→autosave→write.
 */
export async function waitXmlMatch(
  actor: Actor,
  modelId: string,
  pattern: RegExp,
  expected = true,
): Promise<string> {
  let xml = "";
  await expect
    .poll(
      async () => {
        xml = await fetchWorkingCopyXml(actor, modelId);
        return pattern.test(xml);
      },
      { timeout: 20_000, intervals: [400, 800, 1500] },
    )
    .toBe(expected);
  return xml;
}

/** Expande todos os grupos collapsed do painel (re-render incremental). */
export async function expandAllGroups(page: Page) {
  const panel = page.locator(PANEL);
  for (let i = 0; i < 15; i++) {
    const closed = panel.locator(
      ".bio-properties-panel-group-header:not(.open) .bio-properties-panel-group-header-title",
    );
    if (!(await closed.count())) break;
    await closed.first().click();
    await page.waitForTimeout(120);
  }
}

export function entry(page: Page, id: string) {
  return page.locator(`${PANEL} [data-entry-id="${id}"]`);
}

export function entryInput(page: Page, id: string) {
  return entry(page, id).locator("input, textarea").first();
}

/**
 * Text field: click → fill → blur (Tab) para commit do setValue
 * (debounced). Espera o estado dirty do autosave como confirmação do
 * command — sem sleep fixo além do debounce do vendor.
 */
export async function fillEntry(page: Page, id: string, value: string) {
  const input = entryInput(page, id);
  await expect(input).toBeVisible({ timeout: 10_000 });
  await input.click();
  await input.fill(value);
  await input.press("Tab");
  await page.waitForTimeout(400); // debounce do vendor
}

/** Limpa o text field (setValue("")). */
export async function clearEntry(page: Page, id: string) {
  const input = entryInput(page, id);
  await expect(input).toBeVisible({ timeout: 10_000 });
  await input.click();
  await input.fill("");
  await input.press("Tab");
  await page.waitForTimeout(400);
}

export function entryCheckbox(page: Page, id: string) {
  return entry(page, id).locator('input[type="checkbox"]').first();
}

/**
 * Checkbox: clica até o estado desejado persistir no DOM e espera o
 * debounce do setValue → command stack. `check()` do Playwright é
 * idempotente + verifica estado final (sem races com o re-render do
 * painel após expandAllGroups).
 */
export async function setCheckbox(page: Page, id: string, checked: boolean) {
  const box = entryCheckbox(page, id);
  await expect(box).toBeVisible({ timeout: 10_000 });
  if ((await box.isChecked()) !== checked) {
    await box.click();
  }
  if (checked) {
    await expect(box).toBeChecked({ timeout: 5_000 });
  } else {
    await expect(box).not.toBeChecked({ timeout: 5_000 });
  }
  await page.waitForTimeout(400); // debounce do vendor → command
}
