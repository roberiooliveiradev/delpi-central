import { request, type Page } from "@playwright/test";
import {
  test,
  expect,
  apiToken,
  createModelViaApi,
  modelUrl,
  LIBRARY_URL,
  waitSaved,
  PENDING_SAVE_RE,
  requestTokenRefresh,
} from "../helpers";

/**
 * AUTO-x / AUTH-x / NAV-x / UNLOAD-x / REV-x — autosave do Working Copy +
 * continuidade de auth (P-new: token refresh nunca recarrega o editor).
 *
 * Evidence de não-remount: `data-bpmnm-mount-id` no container do canvas —
 * incrementa a cada mount do adapter; refresh deve manter o valor.
 */

async function openEditor(page: Page): Promise<string> {
  const modelId = await createModelViaApi("editor", "E2E-Autosave");
  await page.goto(modelUrl(modelId));
  await waitSaved(page);
  await expect(page.locator(".bpmnm-canvas .djs-container")).toBeVisible();
  return modelId;
}

async function addTask(page: Page, x = 420, y = 220) {
  await page
    .locator('.djs-palette .entry[data-action="create.task"]')
    .click();
  await page
    .locator(".bpmnm-canvas .djs-container")
    .click({ position: { x, y }, force: true });
}

function countPuts(page: Page) {
  const state = { n: 0 };
  page.on("request", (r) => {
    if (r.method() === "PUT" && r.url().includes("/working-copy")) state.n += 1;
  });
  return state;
}

async function apiXml(modelId: string): Promise<string> {
  const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
  const token = await apiToken("editor");
  const ctx = await request.newContext({ baseURL: base });
  const resp = await ctx.get(
    `/apps/bpmn-modeler-api/models/${modelId}/working-copy`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  return resp.text();
}

const mountId = (page: Page) =>
  page.locator(".bpmnm-canvas").first().getAttribute("data-bpmnm-mount-id");

test.describe("AUTO — autosave do working copy", () => {
  test.use({ actor: "editor" });

  test("AUTO-01: edição → debounce → write → read-back → Salvo", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    const puts = countPuts(page);
    await addTask(page);
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      PENDING_SAVE_RE,
      { timeout: 10_000 },
    );
    await waitSaved(page);
    expect(puts.n).toBe(1);
    const xml = await apiXml(modelId);
    expect(xml).toContain("task");
    expect(xml).toContain("BPMNShape");
  });

  test("AUTO-02: burst de comandos → writes coalescidos (sem write storm)", async ({
    page,
  }) => {
    await openEditor(page);
    const puts = countPuts(page);
    // 3 edições rápidas — coalesce em writes limitados
    for (const [i, pos] of [
      [300, 380],
      [560, 380],
      [300, 520],
    ].entries()) {
      await addTask(page, pos[0]!, pos[1]!);
      await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(
        i + 1,
      );
    }
    await waitSaved(page);
    // burst inteiro coalesce: poucos writes, nunca 1:1 com comandos
    expect(puts.n).toBeLessThanOrEqual(2);
    expect(puts.n).toBeGreaterThanOrEqual(1);
  });

  test("AUTO-03: edição durante save in-flight → latest state wins", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    let first = true;
    await page.route("**/working-copy", async (route, req) => {
      if (req.method() === "PUT" && first) {
        first = false;
        await new Promise((r) => setTimeout(r, 1_500));
      }
      await route.continue();
    });
    await addTask(page, 300, 180);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvando…", {
      timeout: 10_000,
    });
    await addTask(page, 520, 180);
    await waitSaved(page, 30_000);
    const xml = await apiXml(modelId);
    // autoritativo contém os dois elementos (estado mais novo, não o do 1º write)
    expect((xml.match(/<bpmn:task|<bpmn2:task/g) ?? []).length).toBe(2);
  });

  test("AUTO-04/05: undo e redo após autosave persistem corretamente", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    await addTask(page);
    await waitSaved(page);
    let xml = await apiXml(modelId);
    expect(xml).toContain("task");

    await page.getByRole("button", { name: "Desfazer" }).click();
    await waitSaved(page);
    xml = await apiXml(modelId);
    expect(xml).not.toContain("<bpmn:task");

    await page.getByRole("button", { name: "Refazer" }).click();
    await waitSaved(page);
    xml = await apiXml(modelId);
    expect(xml).toContain("<bpmn:task");
  });

  test("AUTO-06: Organizar → Aceitar dispara autosave", async ({ page }) => {
    const modelId = await openEditor(page);
    await addTask(page);
    await addTask(page, 600, 180);
    await waitSaved(page);
    const puts = countPuts(page);
    await page.getByRole("button", { name: "Organizar" }).click();
    await expect(
      page.locator('[data-testid="layout-preview"]'),
    ).toBeVisible({ timeout: 20_000 });
    await page
      .locator('[data-testid="layout-preview"]')
      .getByRole("button", { name: "Aceitar" })
      .click();
    await waitSaved(page);
    expect(puts.n).toBeGreaterThanOrEqual(1);
    const xml = await apiXml(modelId);
    expect(xml).toContain("BPMNShape");
  });

  test("AUTO-07: Organizar → Cancelar não dispara autosave", async ({
    page,
  }) => {
    await openEditor(page);
    await addTask(page);
    await waitSaved(page);
    const puts = countPuts(page);
    await page.getByRole("button", { name: "Organizar" }).click();
    await expect(
      page.locator('[data-testid="layout-preview"]'),
    ).toBeVisible({ timeout: 20_000 });
    await page
      .locator('[data-testid="layout-preview"]')
      .getByRole("button", { name: "Cancelar" })
      .click();
    await page.waitForTimeout(3_000); // > debounce
    expect(puts.n).toBe(0);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo");
  });

  test("AUTO-08: edição de propriedade (rename) dispara autosave", async ({
    page,
  }) => {
    const modelId = await openEditor(page);
    await addTask(page);
    await waitSaved(page);
    // rename via direct editing (dblclick → caixa de edição inline)
    const el = page.locator(".bpmnm-canvas .djs-element").first();
    const box = await el.boundingBox();
    await page.mouse.dblclick(box!.x + box!.width / 2, box!.y + box!.height / 2);
    const editing = page.locator(".djs-direct-editing-parent");
    await expect(editing).toBeVisible({ timeout: 8_000 });
    await editing
      .locator("textarea, [contenteditable]")
      .first()
      .fill("Tarefa Autosave");
    await page.keyboard.press("Enter");
    await waitSaved(page);
    const xml = await apiXml(modelId);
    expect(xml).toContain("Tarefa Autosave");
  });

  test("AUTO-09: ações viewport-only não disparam autosave", async ({
    page,
  }) => {
    await openEditor(page);
    const puts = countPuts(page);
    await page.getByRole("button", { name: "Ampliar" }).click();
    await page.getByRole("button", { name: "Reduzir" }).click();
    await page.getByRole("button", { name: "Ajustar à janela" }).click();
    await page.locator(".bpmnm-canvas .djs-container").click({
      position: { x: 60, y: 60 },
    });
    await page.waitForTimeout(3_000); // > debounce
    expect(puts.n).toBe(0);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo");
  });
});

test.describe("AUTH — continuidade de sessão", () => {
  test.use({ actor: "editor" });

  test("AUTH-01/05/06: refresh com editor limpo — sem reload, remount ou prompt", async ({
    page,
  }) => {
    await openEditor(page);
    await addTask(page);
    await waitSaved(page);
    const before = await mountId(page);
    const urlBefore = page.url();

    let dialogs = 0;
    page.on("dialog", (d) => {
      dialogs += 1;
      void d.dismiss();
    });
    await requestTokenRefresh(page);
    await page.waitForTimeout(2_000);

    expect(dialogs).toBe(0);
    expect(page.url()).toBe(urlBefore);
    expect(await mountId(page)).toBe(before);
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(1);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo");
    // command stack intacto: undo disponível e funcional
    await page.getByRole("button", { name: "Desfazer" }).click();
    await waitSaved(page);
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(0);
  });

  test("AUTH-02: refresh enquanto dirty — autosave continua com credencial nova", async ({
    page,
  }) => {
    await openEditor(page);
    const before = await mountId(page);
    await addTask(page);
    // refresh durante a janela dirty (antes do debounce)
    await requestTokenRefresh(page);
    await waitSaved(page);
    expect(await mountId(page)).toBe(before);
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(1);
  });

  test("AUTH-03: refresh durante write in-flight — resultado único, sem remount", async ({
    page,
  }) => {
    await openEditor(page);
    let first = true;
    await page.route("**/working-copy", async (route, req) => {
      if (req.method() === "PUT" && first) {
        first = false;
        await new Promise((r) => setTimeout(r, 1_500));
      }
      await route.continue();
    });
    const before = await mountId(page);
    await addTask(page);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvando…", {
      timeout: 10_000,
    });
    await requestTokenRefresh(page);
    await waitSaved(page, 30_000);
    expect(await mountId(page)).toBe(before);
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(1);
  });

  test("AUTH-04: write 401 → refresh via host → retry → Salvo", async ({
    page,
  }) => {
    await openEditor(page);
    let first = true;
    await page.route("**/working-copy", async (route, req) => {
      if (req.method() === "PUT" && first) {
        first = false;
        await route.fulfill({
          status: 401,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: { code: "AUTHENTICATION_FAILED", message: "expired" },
            meta: { request_id: "t" },
          }),
        });
        return;
      }
      await route.continue();
    });
    await addTask(page);
    await waitSaved(page);
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(1);
  });

  test("AUTH-04b: 401 persistente → Sessão expirada, trabalho preservado", async ({
    page,
  }) => {
    await openEditor(page);
    await page.route("**/working-copy", async (route, req) => {
      if (req.method() === "PUT") {
        await route.fulfill({
          status: 401,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: { code: "AUTHENTICATION_FAILED", message: "expired" },
            meta: { request_id: "t" },
          }),
        });
        return;
      }
      await route.continue();
    });
    await addTask(page);
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      "Sessão expirada",
      { timeout: 20_000 },
    );
    // estado local preservado — nada foi descartado
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(1);
  });

  test("AUTHZ: 403 → fail closed (somente leitura)", async ({ page }) => {
    await openEditor(page);
    await page.route("**/working-copy", async (route, req) => {
      if (req.method() === "PUT") {
        await route.fulfill({
          status: 403,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: { code: "FORBIDDEN", message: "forbidden" },
            meta: { request_id: "t" },
          }),
        });
        return;
      }
      await route.continue();
    });
    await addTask(page);
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      "Somente leitura",
      { timeout: 20_000 },
    );
  });
});

test.describe("OFFLINE/CONFLICT — falhas visíveis e recuperáveis", () => {
  test.use({ actor: "editor" });

  test("OFF-01: falha de rede → Falha/Sem conexão → retry automático ao voltar", async ({
    page,
  }) => {
    await openEditor(page);
    let fail = true;
    await page.route("**/working-copy", async (route, req) => {
      if (req.method() === "PUT" && fail) {
        await route.abort("connectionfailed");
        return;
      }
      await route.continue();
    });
    await addTask(page);
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      /Falha ao salvar|Sem conexão/,
      { timeout: 20_000 },
    );
    // nova edição re-agenda → sucesso → Salvo
    fail = false;
    await addTask(page, 600, 180);
    await waitSaved(page);
    await expect(page.locator(".bpmnm-canvas .djs-element")).toHaveCount(2);
  });

  test("OFF-02: 412/409 → Conflito de edição (sem overwrite silencioso)", async ({
    page,
  }) => {
    await openEditor(page);
    await page.route("**/working-copy", async (route, req) => {
      if (req.method() === "PUT") {
        await route.fulfill({
          status: 412,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: { code: "CONFLICT", message: "version mismatch" },
            meta: { request_id: "t" },
          }),
        });
        return;
      }
      await route.continue();
    });
    await addTask(page);
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      "Conflito de edição",
      { timeout: 20_000 },
    );
    await expect(
      page.getByText(/Outro usuário ou processo alterou/),
    ).toBeVisible();
  });
});

test.describe("NAV/UNLOAD — navegação e ciclo de vida do browser", () => {
  test.use({ actor: "editor" });

  test("NAV-01: navegação interna após Salvo — direto, sem prompt", async ({
    page,
  }) => {
    await openEditor(page);
    await addTask(page);
    await waitSaved(page);
    await page.getByRole("button", { name: "Biblioteca" }).click();
    await page.waitForURL(`**${LIBRARY_URL}`, { timeout: 15_000 });
  });

  test("NAV-02: falha de save → navegação exibe guard do produto", async ({
    page,
  }) => {
    await openEditor(page);
    await page.route("**/working-copy", async (route, req) => {
      if (req.method() === "PUT") {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: { code: "INFRA", message: "boom" },
            meta: { request_id: "t" },
          }),
        });
        return;
      }
      await route.continue();
    });
    await addTask(page);
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      "Falha ao salvar",
      { timeout: 20_000 },
    );
    await page.getByRole("button", { name: "Biblioteca" }).click();
    await expect(
      page.getByText("Alterações não salvas neste modelo"),
    ).toBeVisible({ timeout: 10_000 });
    await page.getByRole("button", { name: "Descartar alterações" }).click();
    await page.waitForURL(`**${LIBRARY_URL}`, { timeout: 15_000 });
  });

  test("UNLOAD-01: estado Salvo → sem handler beforeunload registrado", async ({
    page,
  }) => {
    await openEditor(page);
    await addTask(page);
    await waitSaved(page);
    // dispatch sintético: preventDefault de qualquer handler registrado
    // faria dispatchEvent retornar false — CLEAN não registra proteção.
    const blocked = await page.evaluate(() => {
      const e = new Event("beforeunload", { cancelable: true });
      return !window.dispatchEvent(e) || e.defaultPrevented;
    });
    expect(blocked).toBe(false);
  });

  test("UNLOAD-02: falha genuína → beforeunload registrado (protege close)", async ({
    page,
  }) => {
    await openEditor(page);
    await page.route("**/working-copy", async (route, req) => {
      if (req.method() === "PUT") {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: { code: "INFRA", message: "boom" },
            meta: { request_id: "t" },
          }),
        });
        return;
      }
      await route.continue();
    });
    await addTask(page);
    await expect(page.locator(".bpmnm-save-status")).toHaveText(
      "Falha ao salvar",
      { timeout: 20_000 },
    );
    const blocked = await page.evaluate(() => {
      const e = new Event("beforeunload", { cancelable: true });
      return !window.dispatchEvent(e) || e.defaultPrevented;
    });
    expect(blocked).toBe(true);
  });
});

test.describe("REV — separação working copy / revision", () => {
  test.use({ actor: "manager" });

  test("REV-01: autosave não cria revisão (checkpoint é explícito)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("manager", "E2E-Rev-Autosave");
    await page.goto(modelUrl(modelId));
    await waitSaved(page);
    await addTask(page);
    await addTask(page, 600, 180);
    await waitSaved(page);

    const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
    const token = await apiToken("manager");
    const ctx = await request.newContext({ baseURL: base });
    const resp = await ctx.get(
      `/apps/bpmn-modeler-api/models/${modelId}/revisions`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    const body = await resp.json();
    expect(body.data.items).toHaveLength(0);
  });
});
