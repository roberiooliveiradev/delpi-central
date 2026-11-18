import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = fileURLToPath(new URL("../preview-dist/", import.meta.url));
const origin = "https://studio.test/delpi-central/";
const contentTypes = { ".js": "text/javascript", ".css": "text/css", ".html": "text/html" };
const executablePath = process.env.LBS_CHROMIUM_EXECUTABLE;
const browser = await chromium.launch(executablePath
  ? { executablePath, args: ["--single-process", "--no-zygote"] }
  : {});
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1024 }, colorScheme: "light" });
  await page.route(origin + "**", async route => {
    const name = route.request().url().slice(origin.length) || "index.html";
    await route.fulfill({ path: path.join(root, name), contentType: contentTypes[path.extname(name)] });
  });
  const errors = [];
  const external = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("request", request => { if (!request.url().startsWith(origin)) external.push(request.url()); });
  await page.goto(origin);
  const host = page.locator("delpi-line-balance-studio");
  const metric = name => host.locator(".delpi-ui-kpi-card").filter({ hasText: name }).locator("strong");
  const selectTrigger = name => host.getByRole("combobox", { name, exact: true });
  const options = host.getByRole("listbox");
  const choose = async (name, option) => {
    const trigger = selectTrigger(name);
    await trigger.click();
    assert.equal(await trigger.getAttribute("aria-expanded"), "true");
    await options.getByRole("option", { name: option, exact: true }).click();
    await options.waitFor({ state: "hidden" });
    assert.equal((await trigger.textContent()).trim(), option);
  };
  await host.getByRole("heading", { name: "Yamazumi" }).waitFor();
  const conditionsButton = host.getByRole("button", { name: "Condições de produção" });
  assert.match(await conditionsButton.getAttribute("class"), /delpi-ui-action-btn/);
  assert.match(await selectTrigger("Cenário").getAttribute("class"), /delpi-ui-select__trigger/);
  assert.equal(await host.locator("select").count(), 0);
  assert.equal(await host.locator(".delpi-ui-section-card").count(), 2);
  assert.equal(await host.locator(".delpi-ui-table").count(), 1);
  assert.equal(await host.locator(".delpi-ui-stacked-column-chart").count(), 1);
  assert.equal(await host.locator(".delpi-ui-status-badge").count(), 1);
  await selectTrigger("Cenário").click();
  await options.waitFor();
  assert.equal(await options.evaluate(list => list.getRootNode() instanceof ShadowRoot), true);
  const selectedScenario = options.getByRole("option", { name: "Cenário A · Inicial" });
  assert.equal(await selectedScenario.getAttribute("aria-selected"), "true");
  assert.equal(await selectedScenario.locator("svg").count(), 1);
  await host.getByRole("heading", { name: "Yamazumi" }).click();
  await options.waitFor({ state: "hidden" });
  assert.match(await host.getByLabel("Nome do estudo", { exact: true }).getAttribute("class"), /delpi-ui-native-control/);
  assert.match(await page.locator("#new").getAttribute("class"), /delpi-ui-action-btn/);
  assert.equal(await metric("Takt de referência").textContent(), "70 s");
  assert.equal(await metric("Maior carga").textContent(), "84 s");
  assert.equal(await metric("Sem posto").textContent(), "1");
  await host.evaluate(element => {
    element.addEventListener("study-change", event => {
      element.dataset.lastChangedStudy = event.detail.study.id;
    });
  });
  const segment = host.getByRole("button", { name: /Crimpar terminais, 48 s/ });
  assert.match(await segment.getAttribute("class"), /delpi-ui-chart-segment-button/);
  const drop = host.locator('[data-drop="p3"] .delpi-ui-stacked-column-chart__track');
  await segment.dragTo(drop);
  assert.equal(await host.getAttribute("data-last-changed-study"), "demo");
  assert.equal((await selectTrigger("Posto da operação 4").textContent()).trim(), "Montagem");
  assert.equal(await metric("Maior carga").textContent(), "103 s");
  await choose("Posto da operação 4", "Crimpagem");
  assert.equal(await metric("Maior carga").textContent(), "84 s");
  await choose("Posto da operação 8", "Inspeção");
  assert.match(await host.locator(".delpi-ui-stacked-column-chart__footer").textContent(), /Carga parcial/);
  await choose("Cenário", "Cenário B · Alternativo");
  assert.equal(await metric("Maior carga").textContent(), "70 s");
  await conditionsButton.click();
  assert.equal(await conditionsButton.getAttribute("aria-controls"), "conditions");
  await host.getByLabel("Demanda por turno").fill("300");
  await host.getByRole("button", { name: "+ Adicionar pausa", exact: true }).click();
  await host.getByText("Complete os horários do turno e das pausas.").waitFor();
  assert.equal(await metric("Takt de referência").textContent(), "—");
  await host.getByRole("button", { name: "Remover pausa 3", exact: true }).click();
  assert.equal(await metric("Takt de referência").textContent(), "84 s");
  await choose("Modo de turno", "Minutos");
  await host.getByLabel("Duração (min)").fill("300");
  await host.getByRole("button", { name: "+ Adicionar pausa", exact: true }).click();
  assert.equal(await metric("Tempo produtivo").textContent(), "225 min");
  await page.locator("#new").click();
  await host.getByText("Adicione uma operação para começar.").waitFor();
  await host.getByRole("button", { name: "+ Adicionar operação", exact: true }).click();
  const name = host.getByLabel("Nome da operação 1", { exact: true });
  await name.evaluate(element => {
    if (element.getRootNode().activeElement !== element) throw new Error("O foco precisa ir para a nova operação");
  });
  await name.fill("Peça <teste>");
  await host.getByRole("button", { name: "+ Adicionar posto", exact: true }).click();
  assert.equal(await name.inputValue(), "Peça <teste>");
  await host.getByLabel("Tempo da operação 1 em segundos", { exact: true }).fill("42.5");
  const select = selectTrigger("Posto da operação 1");
  await select.press("ArrowDown");
  const firstOption = options.getByRole("option", { name: "Sem posto", exact: true });
  await firstOption.waitFor();
  await page.waitForFunction(() => document.querySelector("delpi-line-balance-studio").shadowRoot.activeElement?.textContent.trim() === "Sem posto");
  await firstOption.press("ArrowDown");
  await options.getByRole("option", { name: "Posto 1", exact: true }).press("Enter");
  await options.waitFor({ state: "hidden" });
  assert.equal(await metric("Maior carga").textContent(), "42,5 s");
  assert.equal(await host.evaluate(el => el.study.operations[0].name), "Peça <teste>");
  await host.getByRole("button", { name: "Remover posto 1", exact: true }).click();
  assert.equal(await metric("Sem posto").textContent(), "1");
  for (const width of [1024, 390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await page.locator("#example").click();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), width);
    assert.equal(await host.getByRole("heading", { name: "Yamazumi" }).isVisible(), true);
  }
  await page.emulateMedia({ colorScheme: "dark" });
  assert.equal(await host.getByRole("heading", { name: "Yamazumi" }).isVisible(), true);
  await selectTrigger("Cenário").click();
  await options.waitFor();
  assert.equal(await options.evaluate(list => getComputedStyle(list.closest(".delpi-ui-select__panel")).backgroundColor), "rgb(15, 17, 21)");
  await options.getByRole("option").first().press("Escape");
  await options.waitFor({ state: "hidden" });
  for (const theme of ["light", "dark"]) {
    await page.evaluate(value => { document.documentElement.dataset.theme = value; }, theme);
    const themeColors = await host.evaluate(async element => {
      const shadow = element.shadowRoot;
      const controls = [...shadow.querySelectorAll("input, .delpi-ui-select__trigger")];
      for (const control of controls) getComputedStyle(control).backgroundColor;
      await Promise.allSettled(controls.flatMap(control => control.getAnimations().map(animation => animation.finished)));
      const computed = getComputedStyle(document.documentElement);
      const probe = document.createElement("div");
      document.body.append(probe);
      const token = name => {
        probe.style.backgroundColor = `var(${name})`;
        return getComputedStyle(probe).backgroundColor;
      };
      const background = selector => getComputedStyle(shadow.querySelector(selector)).backgroundColor;
      const result = {
        expected: [token("--app-canvas"), token("--surface-2"), token("--surface"), token("--control-bg"), token("--control-bg"), token("--chart-4")],
        actual: [background(".studio"), background(".top"), background(".delpi-ui-kpi-card"), background("input"), background(".delpi-ui-select__trigger"), background(".delpi-ui-chart-segment-button[title^='Crimpar terminais']")],
        mode: getComputedStyle(element).colorScheme,
        canvas: computed.getPropertyValue("--bg").trim(),
      };
      probe.remove();
      return result;
    });
    assert.equal(themeColors.canvas, theme === "light" ? "#ffffff" : "#0f1115");
    assert.equal(themeColors.mode, theme);
    assert.deepEqual(themeColors.actual, themeColors.expected);
  }
  assert.equal(await conditionsButton.evaluate(element => getComputedStyle(element).minHeight), "44px");
  assert.deepEqual(errors, []);
  assert.deepEqual(external, []);
  console.log("PASS Chromium: drag and drop, atribuição por teclado, cenário, tempo desconhecido, pausas, novo estudo, 1440/1024/390/320, tema escuro, sem erros ou tráfego externo");
} finally {
  await browser.close();
}
