import { expect, test } from "@playwright/test";
import { loginAsDev } from "../helpers";

/** E2E UX V3 — «Por página» na toolbar do hero de /apps/helpdesk.
 *
 * HML roda helpdesk-api com GLPI desabilitado (glpi-disabled.hml.invalid)
 * e sessão-fixture seedada para a identidade de homologação: o MFE cai na
 * view «unavailable» (listChrome visível), o que permite validar de
 * verdade no navegador a linha de controles (ordem, geometria, overflow,
 * temas, mudança de page size na URL). Dados GLPI ficam fora do escopo.
 *
 * Breakpoint canônico: viewport ≤ 768px → forceCards (listViewport.ts) —
 * Colunas e o toggle Tabela|Cards saem da linha; «Por página» permanece.
 */
const ROW = ".helpdesk-list-controls-row";
const PAGE_SIZE_BTN = 'button[aria-label*="chamados por página"]';
const FORCE_CARDS_MAX = 768;

async function rowBoxes(page: import("@playwright/test").Page) {
  return page.evaluate(() => {
    const row = document.querySelector(".helpdesk-list-controls-row");
    if (!row) return null;
    const item = (el: Element) => {
      const r = el.getBoundingClientRect();
      return { x: r.x, y: r.y, w: r.width, h: r.height, cx: r.x + r.width / 2 };
    };
    const byText = (re: RegExp) =>
      [...row.querySelectorAll("button")].find((b) => re.test(b.textContent ?? ""));
    const pageSize = row.querySelector('button[aria-label*="chamados por página"]');
    const viewGroup = [...row.querySelectorAll('[role="group"]')].find((g) =>
      g.querySelector("button")?.textContent?.includes("Tabela"),
    );
    const clear = row.querySelector(".delpi-ui-icon-btn--amber");
    return {
      clear: clear ? item(clear) : null,
      filtros: byText(/Filtros/) ? item(byText(/Filtros/)!) : null,
      ordenar: byText(/Ordenar|Última/) ? item(byText(/Ordenar|Última/)!) : null,
      colunas: byText(/Colunas/) ? item(byText(/Colunas/)!) : null,
      pageSize: pageSize ? item(pageSize) : null,
      toggle: viewGroup ? item(viewGroup) : null,
      row: item(row),
      scrollW: document.documentElement.scrollWidth,
      innerW: window.innerWidth,
    };
  });
}

test.describe("Helpdesk UX V3 — Por página na toolbar do hero", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDev(page);
  });

  test("ordem dos controles + FilterX ausente sem filtros + zero overflow", async ({
    page,
  }) => {
    await page.goto("/apps/helpdesk");
    const row = page.locator(ROW);
    await expect(row).toBeVisible({ timeout: 30_000 });

    /* FilterX condicional: sem filtros removíveis, não existe no DOM. */
    await expect(
      row.getByRole("button", { name: /limpar filtros/i }),
    ).toHaveCount(0);

    /* «Por página» presente e único (ToolbarSelectControl do kit). */
    const sel = row.locator(PAGE_SIZE_BTN);
    await expect(sel).toHaveCount(1);
    await expect(sel).toHaveAttribute("aria-haspopup", "listbox");

    const b = await rowBoxes(page);
    expect(b).toBeTruthy();
    const wide = b!.innerW > FORCE_CARDS_MAX;
    expect(b!.filtros && b!.ordenar && b!.pageSize).toBeTruthy();
    expect(b!.filtros!.cx).toBeLessThan(b!.ordenar!.cx);
    if (wide) {
      /* Desktop: FilterX? → Filtros → Ordenar → Colunas → Por página → Tabela|Cards */
      expect(b!.colunas && b!.toggle).toBeTruthy();
      expect(b!.ordenar!.cx).toBeLessThan(b!.colunas!.cx);
      expect(b!.colunas!.cx).toBeLessThan(b!.pageSize!.cx);
      expect(b!.pageSize!.cx).toBeLessThan(b!.toggle!.cx);
    } else {
      /* forceCards (≤768px): Colunas e toggle saem; «Por página» fica após Ordenar. */
      expect(b!.colunas).toBeNull();
      expect(b!.toggle).toBeNull();
      expect(b!.ordenar!.cx).toBeLessThan(b!.pageSize!.cx);
    }
    /* Seletor legível — não comprimido. */
    expect(b!.pageSize!.w).toBeGreaterThanOrEqual(32);
    expect(b!.pageSize!.h).toBeGreaterThanOrEqual(28);
    /* Sem overflow horizontal da página. */
    expect(b!.scrollW).toBeLessThanOrEqual(b!.innerW + 1);
    await page.screenshot({ path: "artifacts/helpdesk-toolbar-order.png", fullPage: false });
  });

  test("FilterX âmbar 36×36 à esquerda de Filtros quando há filtro na URL", async ({
    page,
  }) => {
    await page.goto("/apps/helpdesk?status=open");
    const row = page.locator(ROW);
    const clearBtn = row.getByRole("button", { name: /limpar filtros/i }).first();
    await expect(clearBtn).toBeVisible({ timeout: 30_000 });
    await expect(clearBtn).toHaveClass(/delpi-ui-icon-btn--amber/);

    const b = await rowBoxes(page);
    expect(b!.clear && b!.filtros).toBeTruthy();
    /* 36×36 quadrado — regressão geometry-fix a85c6522b9. */
    expect(Math.abs(b!.clear!.w - 36)).toBeLessThanOrEqual(2);
    expect(Math.abs(b!.clear!.h - 36)).toBeLessThanOrEqual(2);
    /* FilterX imediatamente à esquerda de Filtros. */
    expect(b!.clear!.cx).toBeLessThan(b!.filtros!.cx);
    /* Ícone 16px centrado. */
    const svgBox = await clearBtn.locator("svg").first().boundingBox();
    const btnBox = await clearBtn.boundingBox();
    expect(svgBox && btnBox).toBeTruthy();
    expect(Math.abs(svgBox!.width - 16)).toBeLessThanOrEqual(2);
    expect(
      Math.abs(svgBox!.x + svgBox!.width / 2 - (btnBox!.x + btnBox!.width / 2)),
    ).toBeLessThanOrEqual(2);
    await page.screenshot({ path: "artifacts/helpdesk-filterx-36.png", fullPage: false });
  });

  test("«Por página» abre listbox do kit, atualiza URL (page_size + reset página), instância única", async ({
    page,
  }) => {
    await page.goto("/apps/helpdesk?page=3");
    const row = page.locator(ROW);
    await expect(row).toBeVisible({ timeout: 30_000 });
    const sel = row.locator(PAGE_SIZE_BTN);
    await sel.click();
    const listbox = page.getByRole("listbox");
    await expect(listbox).toBeVisible();
    const options = await listbox.getByRole("button").allTextContents();
    const current = (await sel.textContent())?.replace(/\D/g, "");
    const next = options
      .map((o) => o.replace(/\D/g, ""))
      .filter((o) => o && o !== current)[0];
    expect(next).toBeTruthy();
    await listbox.getByRole("button", { name: next!, exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`page_size=${next}`));
    /* page=1 é o default serializado — commitFilters omite o param,
     * então «voltou à página 1» = param ausente (page=3 removido). */
    await expect(page).not.toHaveURL(/page=[2-9]/);
    expect(new URL(page.url()).searchParams.get("page") ?? "1").toBe("1");
    /* Uma única instância — nenhuma fora do hero. */
    await expect(page.locator(PAGE_SIZE_BTN)).toHaveCount(1);
    await page.screenshot({ path: "artifacts/helpdesk-page-size-url.png", fullPage: false });
  });

  test("Tabela|Cards preserva o seletor e o estado", async ({ page }) => {
    await page.goto("/apps/helpdesk");
    const row = page.locator(ROW);
    await expect(row).toBeVisible({ timeout: 30_000 });
    const cards = row.getByRole("button", { name: "Cards", exact: true });
    const table = row.getByRole("button", { name: "Tabela", exact: true });
    test.skip(
      (page.viewportSize()?.width ?? 0) <= FORCE_CARDS_MAX,
      "forceCards ≤768px — toggle ausente por breakpoint canônico",
    );
    await cards.click();
    await expect(row.locator(PAGE_SIZE_BTN)).toHaveCount(1);
    await page.screenshot({ path: "artifacts/helpdesk-cards-mode.png", fullPage: false });
    await table.click();
    await expect(row.locator(PAGE_SIZE_BTN)).toHaveCount(1);
  });

  test("tema escuro mantém visibilidade dos controles", async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem("theme", "dark"));
    await page.goto("/apps/helpdesk");
    const row = page.locator(ROW);
    await expect(row).toBeVisible({ timeout: 30_000 });
    await expect(row.locator(PAGE_SIZE_BTN)).toBeVisible();
    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme"),
    );
    expect(theme).toBe("dark");
    await page.screenshot({ path: "artifacts/helpdesk-dark.png", fullPage: false });
  });
});
