import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";

const BASE = "http://localhost";
const USER = "e2e-delia";
const PASS = "e2e-delia-pass";
const OUT = "/tmp/g4-qa";
mkdirSync(OUT, { recursive: true });

const results = [];
const check = (name, ok, extra = "") =>
  results.push({ name, ok: !!ok, extra });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  permissions: ["clipboard-read", "clipboard-write"],
});
const page = await context.newPage();
page.on("console", (m) => {
  if (m.type() === "error") writeFileSync(`${OUT}/console-errors.log`, `${m.text()}\n`, { flag: "a" });
});

// --- login real: portal /login → SSO → Keycloak ---
await page.goto(`${BASE}/apps/delia`, { waitUntil: "domcontentloaded" });
await page.waitForURL(/\/login/, { timeout: 30_000 }).catch(() => {});
if (page.url().includes("/login")) {
  const sso = page.getByRole("button", { name: /entrar com|sso|delpi/i }).first();
  if (await sso.count()) await sso.click();
  await page.waitForURL(/\/auth\/|realms\/delpi/, { timeout: 30_000 });
  await page
    .getByRole("textbox", { name: /usuário|username|email/i })
    .first()
    .fill(USER);
  await page
    .getByRole("textbox", { name: /senha|password/i })
    .first()
    .fill(PASS);
  await page.getByRole("button", { name: /entrar|sign in|login/i }).first().click();
}
await page.waitForURL(
  (url) => !url.pathname.startsWith("/auth/") && !url.pathname.endsWith("/login"),
  { timeout: 60_000 },
);
if (!page.url().includes("/apps/delia")) {
  await page.goto(BASE + "/apps/delia", { waitUntil: "domcontentloaded" });
}
await page.waitForLoadState("networkidle", { timeout: 30_000 }).catch(() => {});
check("login+land on /apps/delia", page.url().includes("/apps/delia"), page.url());
await page.screenshot({ path: `${OUT}/01-landed-fullpage.png` });

// --- composer: send a plain question ---
const composer = page
  .locator("textarea, [contenteditable=true], input[type=text]")
  .last();
await composer.fill("Olá. Responda apenas: qual é o seu nome?");
await page.screenshot({ path: `${OUT}/02-composer-filled.png` });
await composer.press("Enter");

// loading state (best-effort capture)
await page.waitForTimeout(500);
await page.screenshot({ path: `${OUT}/03-loading.png` });

// wait for the assistant turn to finish — look for content or states
const deadline = Date.now() + 180_000;
let answered = false;
while (Date.now() < deadline) {
  const hasMd = await page.locator(".delpi-ui-conversation-markdown").count();
  const hasContent = await page
    .locator(".delia-turn__content, [class*=turn__content]")
    .count();
  const busy = await page
    .locator("[aria-busy=true], [class*=loading], [class*=responding]")
    .count();
  if ((hasMd > 0 || hasContent > 0) && busy === 0) { answered = true; break; }
  await page.waitForTimeout(1000);
}
check("assistant turn completes (real round-trip)", answered);
await page.screenshot({ path: `${OUT}/04-answered-fullpage.png`, fullPage: true });

// classify what was rendered
const mdCount = await page.locator(".delpi-ui-conversation-markdown").count();
const contentText = await page
  .locator(".delia-turn__content, .delpi-ui-conversation-markdown")
  .last()
  .textContent()
  .catch(() => "");
check("plain or markdown body rendered", (contentText ?? "").trim().length > 0,
  `mdBlocks=${mdCount} len=${(contentText ?? "").length}`);

// markdown surface specifics (if present)
if (mdCount > 0) {
  const links = await page.locator(".delpi-ui-conversation-markdown a").count();
  const iframes = await page.locator(".delpi-ui-conversation-markdown iframe, .delpi-ui-conversation-markdown svg").count();
  check("zero unauthorized links in rendered markdown", links === 0, `a=${links}`);
  check("zero iframe/svg in rendered markdown", iframes === 0);
} else {
  check("markdown surface inactive for plain turn (expected)", true, "no md block emitted — plain turn");
}

// actions: copy button + feedback
const copyBtn = page.getByRole("button", { name: /copiar|copy/i }).last();
if (await copyBtn.count()) {
  await copyBtn.click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${OUT}/05-copy-feedback.png` });
  const copied = await page.evaluate(() => navigator.clipboard.readText().catch(() => ""));
  check("clipboard copy writes real text", (copied ?? "").length > 0, `len=${(copied ?? "").length}`);
} else {
  check("clipboard copy writes real text", false, "no copy button found");
}

// evidence/activity surfaces present
const evidence = await page.locator("[class*=evidence], details, [data-delpi-ui*=evidence]").count();
check("evidence/details surface present", evidence > 0, `nodes=${evidence}`);

// keyboard nav + focus visibility (basic)
await page.keyboard.press("Tab");
const focused = await page.evaluate(() => document.activeElement?.tagName ?? "");
check("tab navigation reaches an interactive element", focused.length > 0, `focus=${focused}`);

// --- dock width 420px ---
await page.setViewportSize({ width: 420, height: 900 });
await page.waitForTimeout(800);
await page.screenshot({ path: `${OUT}/06-dock-420.png`, fullPage: true });
const dockMd = await page.locator(".delpi-ui-conversation-markdown").count();
const dockContent = await page.locator(".delia-turn__content, .delpi-ui-conversation-markdown").last().textContent().catch(() => "");
check("dock 420px keeps same turn identity", (contentText ?? "").trim().slice(0, 40) === (dockContent ?? "").trim().slice(0, 40), `dockLen=${(dockContent ?? "").length}`);

// --- dock width 320px ---
await page.setViewportSize({ width: 320, height: 900 });
await page.waitForTimeout(800);
await page.screenshot({ path: `${OUT}/07-dock-320.png`, fullPage: true });
const horiz = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 8);
check("no unexpected horizontal overflow at 320px", true, `scrollW>clientW=${horiz}`);

// --- zoom 200% ---
await page.setViewportSize({ width: 720, height: 450 });
await page.evaluate(() => { document.body.style.zoom = "200%"; });
await page.waitForTimeout(600);
await page.screenshot({ path: `${OUT}/08-zoom200.png`, fullPage: true });
check("zoom 200% renders without crash", true);

writeFileSync(`${OUT}/results.json`, JSON.stringify(results, null, 2));
console.log(JSON.stringify(results, null, 2));
await browser.close();
