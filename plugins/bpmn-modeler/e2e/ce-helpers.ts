/**
 * G2B — helpers de jornada CREATE_EDIT.
 *
 * read-back autoritativo via API (GET working-copy = XML raw) + reload do
 * editor como prova de persistência/DI — nunca apenas DOM/canvas em
 * memória.
 */
import { expect, request, type Page } from "@playwright/test";
import { apiToken, waitSaved, modelUrl, type Actor } from "./helpers";

const BASE = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";

/** XML autoritativo do working copy persistido (GET = raw BPMN+DI). */
export async function fetchWorkingCopyXml(
  actor: Actor,
  modelId: string,
): Promise<string> {
  const token = await apiToken(actor);
  const ctx = await request.newContext({ baseURL: BASE });
  const resp = await ctx.get(
    `/apps/bpmn-modeler-api/models/${modelId}/working-copy`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!resp.ok())
    throw new Error(`working-copy GET failed: ${resp.status()}`);
  return resp.text();
}

export async function openEditor(page: Page, modelId: string) {
  await page.goto(modelUrl(modelId));
  await expect(page.locator(".bpmnm-canvas .djs-container")).toBeVisible({
    timeout: 20_000,
  });
  await waitSaved(page);
}

export async function canvasBox(page: Page) {
  const box = await page.locator(".bpmnm-canvas .djs-container").boundingBox();
  if (!box) throw new Error("canvas not found");
  return box;
}

export async function elBox(page: Page, elementId: string) {
  const box = await page
    .locator(`.djs-element[data-element-id="${elementId}"]`)
    .boundingBox();
  if (!box) throw new Error(`element ${elementId} not found`);
  return box;
}

/**
 * Seleciona elemento e abre o context pad.
 * Clique default = centro (losango de gateway: canto do bbox cai fora da
 * forma e seleciona a sequenceFlow por baixo). Pools: passar posição no
 * header (ex.: { x: 20, y: 12 }) — o centro cai na lane/processo interno.
 */
export async function clickEl(
  page: Page,
  elementId: string,
  position?: { x: number; y: number },
) {
  const el = page.locator(`.djs-element[data-element-id="${elementId}"]`);
  const box = await el.boundingBox();
  if (!box) throw new Error(`element ${elementId} not found`);
  // O bbox do .djs-element inclui o label externo (abaixo de gateways/
  // eventos) e a hit-area invisível das sequenceFlows cruza o interior do
  // shape — um único ponto pode selecionar o elemento errado. Tenta
  // pontos candidatos até o elemento alvo ficar selecionado.
  const candidates = position
    ? [position]
    : [
        { x: box.width / 2, y: Math.min(box.height / 2, 24) },
        { x: box.width * 0.72, y: Math.min(box.height * 0.2, 20) },
        { x: box.width * 0.28, y: Math.min(box.height * 0.2, 20) },
        { x: 15, y: 12 },
      ];
  const sel = page.locator(
    `.djs-element.selected[data-element-id="${elementId}"]`,
  );
  for (const pos of candidates) {
    await el.click({ position: pos, force: true });
    await page.waitForTimeout(80);
    if (await sel.count()) break;
  }
  await expect(sel).toBeAttached({ timeout: 10_000 });
  await expect(page.locator(".djs-context-pad.open")).toBeVisible({
    timeout: 10_000,
  });
}

/**
 * Clique em área vazia dentro do canvas → deseleciona (e foca o svg).
 * O vendor às vezes não emite element.click no 1º clique pós-create/drag
 * (drag intent no mousedown engole o up) — retenta até deselecionar.
 */
export async function deselect(
  page: Page,
  pos = { x: 520, y: 430 },
) {
  await expect(async () => {
    await page
      .locator(".bpmnm-canvas .djs-container")
      .click({ position: pos });
    await page.waitForTimeout(150);
    expect(await page.locator(".djs-element.selected").count()).toBe(0);
  }).toPass({ timeout: 6_000, intervals: [300, 600, 1000] });
}

/**
 * Seleção via DOM real (dispatch click no grupo visual) — fallback para
 * elementos pequenos/apertados onde o hit-test por coordenada pega o
 * vizinho errado (labels, flows cruzando, diagrama reduzido por
 * fitViewport). Mesmo mecanismo do fallback de `replaceWith`: o click
 * borbulha ao container e o vendor resolve o djs-element ancestral.
 * `shift` adiciona à seleção existente (multi-select).
 */
export async function selectViaDom(
  page: Page,
  elementId: string,
  shift = false,
) {
  const sel = page.locator(
    `.djs-element.selected[data-element-id="${elementId}"]`,
  );
  // idempotente: se já está selecionado (ex.: cut negado deixa a seleção
  // intacta), um novo click poderia desmarcar
  if (!shift && (await sel.count()) > 0) return;
  await page.evaluate(
    ({ elementId, shift }) => {
      const g = document.querySelector(
        `.djs-element[data-element-id="${elementId}"]`,
      );
      const target = g?.querySelector("*") ?? g;
      target?.dispatchEvent(
        new MouseEvent("click", { bubbles: true, shiftKey: shift }),
      );
      // o keyboard do vendor é bound ao SVG (tabindex=0) — dispatchEvent
      // não move foco; sem isto Ctrl+C/X/V nunca alcançam o handler
      (
        document.querySelector(".bpmnm-canvas svg") as HTMLElement | null
      )?.focus();
    },
    { elementId, shift },
  );
  await expect(sel).toBeAttached({ timeout: 5_000 });
}

/** Palette create entry → clique no canvas para posicionar. */
export async function createFromPalette(
  page: Page,
  action: string,
  x: number,
  y: number,
) {
  await page
    .locator(`.djs-palette .entry[data-action="${action}"]`)
    .click();
  await page.locator(".bpmnm-canvas .djs-container").click({
    position: { x, y },
  });
  await closeDirectEditing(page);
}

/**
 * Garante foco no <svg> do canvas — o keyboard do vendor é bound a ele
 * (tabindex=0) e atalhos morrem quando activeElement é body/input do
 * properties panel. Equivale ao usuário clicando no canvas.
 */
export async function focusCanvasSvg(page: Page) {
  await page.evaluate(() => {
    (
      document.querySelector(
        ".bpmnm-canvas .djs-container > svg",
      ) as HTMLElement | null
    )?.focus();
  });
  await expect(
    page.locator(".bpmnm-canvas .djs-container > svg"),
  ).toBeFocused();
}

/**
 * O vendor abre direct editing automaticamente após criar elementos com
 * label (foco vai para .djs-direct-editing-content — atalhos do canvas
 * morrem ali). Escape cancela o rename mantendo o elemento criado.
 * No-op quando o overlay não abriu (ex.: data objects).
 */
export async function closeDirectEditing(page: Page) {
  const de = page.locator(".djs-direct-editing-content");
  if (await de.isVisible().catch(() => false)) {
    await page.keyboard.press("Escape");
    await expect(de).not.toBeVisible();
    // o vendor agenda canvas.restoreFocus() debounced — o próximo
    // keystroke do teste pode correr antes; torna o foco determinístico
    await focusCanvasSvg(page);
  }
}

export async function padAction(page: Page, action: string) {
  await page
    .locator(`.djs-context-pad.open .entry[data-action="${action}"]`)
    .click();
}

/**
 * Context pad append → novo elemento segue o cursor → clique posiciona.
 * Retorna posição usada.
 */
export async function appendAndPlace(
  page: Page,
  action: string,
  x: number,
  y: number,
) {
  await padAction(page, action);
  await page.locator(".bpmnm-canvas .djs-container").click({
    position: { x, y },
  });
}

/** Replace menu → entry do popup (data-id="replace-with-*"). */
export async function replaceWith(page: Page, entryId: string) {
  const popup = page.locator(".djs-popup");
  await padAction(page, "replace");
  if (!(await popup.isVisible().catch(() => false))) {
    // fallback: real click na pad entry não abriu o popup (hit-test em
    // entry draggable — observado em participant); delega o mesmo
    // handler 'click' do produto via DOM.
    await page.evaluate(() => {
      (
        document.querySelector(
          '.djs-context-pad.open .entry[data-action="replace"]',
        ) as HTMLElement | null
      )?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
  }
  const entry = page.locator(`.djs-popup [data-id="${entryId}"]`).first();
  await expect(entry).toBeVisible({ timeout: 10_000 });
  await entry.click();
}

/** Connect tool do context pad → drag até o elemento alvo. */
export async function connectElements(
  page: Page,
  sourceId: string,
  targetId: string,
) {
  await clickEl(page, sourceId);
  const connect = page.locator(
    '.djs-context-pad.open .entry[data-action="connect"]',
  );
  try {
    await expect(connect).toBeVisible({ timeout: 10_000 });
  } catch (e) {
    const dbg = await page.evaluate(() => ({
      pad: [...document.querySelectorAll(".djs-context-pad.open .entry")].map(
        (n) => n.getAttribute("data-action"),
      ),
      selected: [...document.querySelectorAll(".djs-element.selected")].map(
        (n) => n.getAttribute("data-element-id"),
      ),
    }));
    console.log("PAD-DEBUG", JSON.stringify(dbg));
    throw e;
  }
  const c = await connect.boundingBox();
  const t = await elBox(page, targetId);
  await page.mouse.move(c!.x + c!.width / 2, c!.y + c!.height / 2);
  await page.mouse.down();
  await page.mouse.move(t.x + t.width / 2, t.y + t.height / 2, { steps: 8 });
  await page.mouse.up();
}

/** Rename via direct edit (dblclick → digita → Enter). */
export async function renameElement(
  page: Page,
  elementId: string,
  text: string,
) {
  await clickEl(page, elementId);
  const box = await elBox(page, elementId);
  await page.mouse.dblclick(box.x + box.width / 2, box.y + box.height / 2);
  await page.keyboard.type(text);
  await page.keyboard.press("Enter");
}

/** Assert estrutural no XML (prefix-agnostic para QNames). */
export function expectXmlHas(xml: string, pattern: RegExp, label: string) {
  expect(xml, `XML read-back sem ${label}`).toMatch(pattern);
}

/** Ciclo completo: autosave → XML autoritativo → reload → elemento renderiza. */
export async function saveReadbackReload(
  page: Page,
  actor: Actor,
  modelId: string,
  elementIds: string[],
): Promise<string> {
  await waitSaved(page);
  const xml = await fetchWorkingCopyXml(actor, modelId);
  await page.reload();
  await expect(page.locator(".bpmnm-canvas .djs-container")).toBeVisible({
    timeout: 20_000,
  });
  for (const id of elementIds) {
    await expect(
      page.locator(`.djs-element[data-element-id="${id}"]`),
      `elemento ${id} não reapareceu após reload`,
    ).toBeAttached({ timeout: 15_000 });
  }
  return xml;
}

/** id do elemento atualmente selecionado (novo elemento criado). */
export async function selectedElementId(page: Page): Promise<string> {
  const sel = page.locator(".djs-element.selected").first();
  await expect(sel).toBeAttached({ timeout: 10_000 });
  const id = await sel.getAttribute("data-element-id");
  if (!id) throw new Error("selected element without id");
  return id;
}

/**
 * Dropa um intermediate event da palette NA BORDA de uma activity →
 * boundary event. Aguarda o marker `attach-ok` no host antes de soltar
 * (sem o marker o create tool descarta o drop).
 */
export async function attachBoundary(
  page: Page,
  hostId: string,
  edge: "bottom" | "top" | "left" | "right" = "bottom",
): Promise<string> {
  const before = new Set(await shapeIds(page));
  const tb = await elBox(page, hostId);
  await page
    .locator('.djs-palette .entry[data-action="create.intermediate-event"]')
    .click();
  const px = {
    bottom: { x: tb.x + tb.width / 3, y: tb.y + tb.height - 1 },
    top: { x: tb.x + tb.width / 3, y: tb.y + 1 },
    left: { x: tb.x + 1, y: tb.y + tb.height / 2 },
    right: { x: tb.x + tb.width - 1, y: tb.y + tb.height / 2 },
  }[edge];
  await page.mouse.move(px.x, px.y);
  await page
    .locator(`.djs-element[data-element-id="${hostId}"].attach-ok`)
    .waitFor({ timeout: 5_000 });
  await page.mouse.down();
  await page.mouse.up();
  let created: string | undefined;
  await expect
    .poll(
      async () => {
        created = (await shapeIds(page)).find((id) => !before.has(id));
        return created ?? null;
      },
      { timeout: 10_000 },
    )
    .not.toBeNull();
  return created!;
}

/** ids de SHAPES no DOM (exclui connections — flows também são .djs-element). */
export async function shapeIds(page: Page): Promise<string[]> {
  return page.evaluate(() =>
    [...document.querySelectorAll(".djs-element.djs-shape")]
      .map((n) => n.getAttribute("data-element-id"))
      .filter(Boolean) as string[],
  );
}

/**
 * Executa `action` e retorna o id da nova CONNECTION criada
 * (sequenceFlow/messageFlow/association/dataAssociation — diff de DOM).
 */
export async function newConnectionId(
  page: Page,
  action: () => Promise<void>,
): Promise<string> {
  const ids = () =>
    page.evaluate(() =>
      [...document.querySelectorAll(".djs-element.djs-connection")]
        .map((n) => n.getAttribute("data-element-id"))
        .filter(Boolean) as string[],
    );
  const before = new Set(await ids());
  await action();
  let created: string | undefined;
  await expect
    .poll(
      async () => {
        created = (await ids()).find((id) => !before.has(id));
        return created ?? null;
      },
      { timeout: 10_000 },
    )
    .not.toBeNull();
  return created!;
}

/**
 * Executa `action` e retorna o id do novo shape criado (diff de DOM —
 * não depende do estado de seleção).
 */
export async function newShapeId(
  page: Page,
  action: () => Promise<void>,
): Promise<string> {
  const before = new Set(await shapeIds(page));
  await action();
  let created: string | undefined;
  await expect
    .poll(
      async () => {
        created = (await shapeIds(page)).find((id) => !before.has(id));
        return created ?? null;
      },
      { timeout: 10_000 },
    )
    .not.toBeNull();
  return created!;
}
