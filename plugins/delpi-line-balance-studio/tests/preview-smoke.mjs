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
  const metric = name => host.locator(".metric").filter({ hasText: name }).locator("strong");
  await host.getByRole("heading", { name: "Yamazumi" }).waitFor();
  assert.equal(await metric("Takt de referência").textContent(), "70 s");
  assert.equal(await metric("Maior carga").textContent(), "84 s");
  assert.equal(await metric("Sem posto").textContent(), "1");
  await host.evaluate(element => {
    element.addEventListener("study-change", event => {
      element.dataset.lastChangedStudy = event.detail.study.id;
    });
  });
  const segment = host.getByRole("button", { name: /Crimpar terminais, 48 segundos/ });
  const drop = host.locator('[data-drop="p3"] .track');
  await segment.dragTo(drop);
  assert.equal(await host.getAttribute("data-last-changed-study"), "demo");
  assert.equal(await host.getByLabel("Posto da operação 4", { exact: true }).inputValue(), "p3");
  assert.equal(await metric("Maior carga").textContent(), "103 s");
  await host.getByLabel("Posto da operação 4", { exact: true }).selectOption("p2");
  assert.equal(await metric("Maior carga").textContent(), "84 s");
  await host.getByLabel("Posto da operação 8", { exact: true }).selectOption("p4");
  assert.match(await host.locator(".chart-footer").textContent(), /Carga parcial/);
  await host.getByLabel("Cenário", { exact: true }).selectOption("b");
  assert.equal(await metric("Maior carga").textContent(), "70 s");
  await host.getByRole("button", { name: "Condições de produção" }).click();
  await host.getByLabel("Demanda por turno").fill("300");
  await host.getByRole("button", { name: "+ Adicionar pausa", exact: true }).click();
  await host.getByText("Complete os horários do turno e das pausas.").waitFor();
  assert.equal(await metric("Takt de referência").textContent(), "—");
  await host.getByRole("button", { name: "Remover pausa 3", exact: true }).click();
  assert.equal(await metric("Takt de referência").textContent(), "84 s");
  await host.getByLabel("Modo de turno").selectOption("MINUTES");
  await host.getByLabel("Duração (min)").fill("300");
  await host.getByRole("button", { name: "+ Adicionar pausa", exact: true }).click();
  assert.equal(await metric("Tempo produtivo").textContent(), "225 min");
  await page.locator("#new").click();
  await host.getByText("Adicione uma operação para começar.").waitFor();
  await host.getByRole("button", { name: "+ Adicionar operação", exact: true }).click();
  const name = host.getByLabel("Nome da operação 1", { exact: true });
  await name.fill("Peça <teste>");
  await host.getByRole("button", { name: "+ Adicionar posto", exact: true }).click();
  assert.equal(await name.inputValue(), "Peça <teste>");
  await host.getByLabel("Tempo da operação 1 em segundos", { exact: true }).fill("42");
  await host.getByLabel("Posto da operação 1", { exact: true }).focus();
  const select = host.getByLabel("Posto da operação 1", { exact: true });
  await select.press("ArrowDown");
  await select.press("Enter");
  assert.equal(await metric("Maior carga").textContent(), "42 s");
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
  assert.deepEqual(errors, []);
  assert.deepEqual(external, []);
  console.log("PASS Chromium: drag and drop, atribuição por teclado, cenário, tempo desconhecido, pausas, novo estudo, 1440/1024/390/320, tema escuro, sem erros ou tráfego externo");
} finally {
  await browser.close();
}
