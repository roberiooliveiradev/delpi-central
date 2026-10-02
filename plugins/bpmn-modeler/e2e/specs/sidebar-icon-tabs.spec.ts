import { test, expect, importModelViaApi, modelUrl } from "../helpers";
import type { Page } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

/**
 * E2E-46 — sidebar top navigation icon-only.
 *
 * As tabs da sidebar usam `iconOnly` do UnderlineNav do plugin-ui:
 * visualmente só o glyph, mas o label permanece no DOM como sr-only
 * (accessible name PT-BR intacto), `title` traz o help e a semântica
 * de tablist/tab/roving-tabindex é a mesma de antes.
 */

const XML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_ic" targetNamespace="urn:ic">' +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1" name="Tarefa"/><bpmn:endEvent id="E1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="E1"/>' +
  '</bpmn:process>' +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="140" y="140" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="240" y="120" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E1_di" bpmnElement="E1"><dc:Bounds x="400" y="140" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="176" y="158"/><di:waypoint x="240" y="158"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F2_di" bpmnElement="F2"><di:waypoint x="340" y="158"/><di:waypoint x="400" y="158"/></bpmndi:BPMNEdge>' +
  '</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>';

const SHOTS = path.resolve(import.meta.dirname, "../../.tmp-shots");

const TABS = [
  ["Propriedades", "Ver e editar as propriedades do elemento selecionado."],
  ["Validação", "Ver problemas e avisos encontrados no modelo."],
  ["Histórico", "Consultar e restaurar revisões do modelo."],
] as const;

async function openEditor(page: Page, theme: "light" | "dark" = "dark") {
  await page.evaluate((t) => {
    localStorage.setItem("theme", t);
    document.documentElement.setAttribute("data-theme", t);
  }, theme);
  const modelId = await importModelViaApi("editor", "E2E-IconTabs", XML);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(600);
}

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`) });
}

test.describe("E2E-46 — sidebar icon-only tabs", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  test("ICT-01: 3 tabs icon-only — sr-only labels, sem texto visível", async ({
    page,
  }) => {
    await openEditor(page);
    const tabs = page.locator('.bpmnm-side__tabs [role="tab"]');
    await expect(tabs).toHaveCount(3);

    for (const [name, help] of TABS) {
      const tab = page.getByRole("tab", { name, exact: true });
      await expect(tab).toBeVisible();
      await expect(tab.locator("svg")).toHaveCount(1);
      // accessible name + tooltip PT-BR
      expect(await tab.getAttribute("title")).toContain(help);
      // label sr-only: presente no DOM mas sem box visível
      const label = tab.locator('[class*="underline-nav__label"]');
      const lb = await label.boundingBox();
      expect(lb === null || lb.width <= 1).toBeTruthy();
    }

    // nenhuma tab renderiza o texto visualmente (largura compacta)
    const widths = await tabs.evaluateAll((els) =>
      els.map((el) => (el as HTMLElement).getBoundingClientRect().width),
    );
    for (const w of widths) {
      expect(w).toBeGreaterThanOrEqual(38); // hit target mínimo
      expect(w).toBeLessThanOrEqual(60); // icon-only compacto
    }
    await shot(page, "sidebar-tabs-icons-dark");
  });

  test("ICT-02: roving tabindex + arrows trocam a tab", async ({ page }) => {
    await openEditor(page);
    const tablist = page.locator('.bpmnm-side__tabs [role="tablist"]');
    await expect(tablist).toBeVisible();

    const props = page.getByRole("tab", { name: "Propriedades" });
    const valid = page.getByRole("tab", { name: "Validação" });
    const hist = page.getByRole("tab", { name: "Histórico" });

    // roving tabindex: só a ativa é tabbable
    expect(await props.getAttribute("tabindex")).toBe("0");
    expect(await valid.getAttribute("tabindex")).toBe("-1");

    await props.focus();
    await page.keyboard.press("ArrowRight");
    await expect(valid).toHaveAttribute("aria-selected", "true");
    expect(await valid.getAttribute("tabindex")).toBe("0");
    await shot(page, "sidebar-validation-active");

    await page.keyboard.press("ArrowRight");
    await expect(hist).toHaveAttribute("aria-selected", "true");
    await shot(page, "sidebar-history-active");

    await page.keyboard.press("ArrowLeft");
    await expect(valid).toHaveAttribute("aria-selected", "true");
  });

  test("ICT-03: active state estrutural (underline) — não só cor", async ({
    page,
  }) => {
    await openEditor(page);
    const active = page.getByRole("tab", { name: "Propriedades" });
    // indicador ativo = box-shadow inset -2px accent (estrutural)
    const shadow = await active.evaluate(
      (el) => getComputedStyle(el).boxShadow,
    );
    expect(shadow).toContain("inset");
    expect(shadow).not.toBe("none");
    await shot(page, "sidebar-properties-active");
  });

  test("ICT-04: collapse não é tab e permanece separado", async ({ page }) => {
    await openEditor(page);
    // controle de collapse fora do tablist
    const inTablist = await page
      .locator('[role="tablist"] button[aria-label="Recolher painel lateral"]')
      .count();
    expect(inTablist).toBe(0);
    const collapse = page.locator('button[aria-label="Recolher painel lateral"]');
    await expect(collapse).toBeVisible();
    // sem indicador de tab (sem aria-selected / box-shadow de underline)
    expect(await collapse.getAttribute("aria-selected")).toBeNull();
  });

  test("ICT-05: sem overflow horizontal na head/nav", async ({ page }) => {
    await openEditor(page);
    for (const sel of [".bpmnm-side__head", ".bpmnm-side__tabs"]) {
      const ok = await page.locator(sel).evaluate(
        (el) => el.scrollWidth <= el.clientWidth,
      );
      expect(ok, `${sel} overflow`).toBe(true);
    }
  });

  test("ICT-06: rail usa os mesmos glyphs/tooltips", async ({ page }) => {
    await openEditor(page);
    await page.locator('button[aria-label="Recolher painel lateral"]').click();
    await page.waitForTimeout(400);

    for (const [name, help] of TABS) {
      const btn = page.locator(
        `.bpmnm-side__rail button[aria-label="${name}"]`,
      );
      await expect(btn).toBeVisible();
      await expect(btn.locator("svg")).toHaveCount(1);
      expect(
        await btn.evaluate((el) => el.parentElement?.getAttribute("title")),
      ).toContain(help);
    }
    await shot(page, "sidebar-collapsed-icons");

    // click na rail expande direto na aba
    await page
      .locator('.bpmnm-side__rail button[aria-label="Histórico"]')
      .click();
    await page.waitForTimeout(400);
    await expect(
      page.getByRole("tab", { name: "Histórico" }),
    ).toHaveAttribute("aria-selected", "true");
    await shot(page, "sidebar-expanded-icons");
  });

  test("ICT-08: tooltips (title PT-BR) + hover surface", async ({ page }) => {
    await openEditor(page);
    for (const [name, help] of TABS) {
      const tab = page.getByRole("tab", { name, exact: true });
      expect(await tab.getAttribute("title")).toBe(help);
      await tab.hover();
      await page.waitForTimeout(400);
      await shot(
        page,
        `sidebar-tooltip-${name === "Propriedades" ? "properties" : name === "Validação" ? "validation" : "history"}`,
      );
      // hover aplica surface (background diferente do transparent)
      const bg = await tab.evaluate(
        (el) => getComputedStyle(el).backgroundColor,
      );
      expect(bg).not.toBe("rgba(0, 0, 0, 0)");
    }
  });

  test("ICT-07: light + zoom 125%", async ({ page }) => {
    await openEditor(page, "light");
    await shot(page, "sidebar-tabs-icons-light");
    await page.evaluate(
      () => ((document.body.style as any).zoom = "1.25"),
    );
    await page.waitForTimeout(400);
    const nav = page.locator(".bpmnm-side__tabs");
    const ok = await nav.evaluate((el) => el.scrollWidth <= el.clientWidth);
    expect(ok).toBe(true);
    await shot(page, "zoom125-sidebar-icons");
  });
});
