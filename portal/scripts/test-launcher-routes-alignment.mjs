import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturePath = path.join(__dirname, "launcher-routes-alignment-fixture.html");
const fixtureUrl = `file://${fixturePath}`;

const MAX_CENTER_DELTA_PX = 2;

const browser = await chromium.launch({
  headless: true,
  executablePath:
    process.env.PLAYWRIGHT_CHROME_EXECUTABLE_PATH ||
    `${process.env.HOME}/.cache/ms-playwright/chromium-1169/chrome-linux/chrome`,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

await page.goto(fixtureUrl, { waitUntil: "networkidle" });
await page.waitForTimeout(500);

const metrics = await page.evaluate(() => {
  const tile = document.getElementById("tile");
  const routes = document.getElementById("routes");
  if (!tile || !routes) {
    return { error: "Elementos de teste não encontrados." };
  }

  const tileRect = tile.getBoundingClientRect();
  const routesRect = routes.getBoundingClientRect();

  const tileCenter = tileRect.left + tileRect.width / 2;
  const routesCenter = routesRect.left + routesRect.width / 2;
  const delta = Math.abs(tileCenter - routesCenter);

  return {
    tile: {
      left: tileRect.left,
      width: tileRect.width,
      center: tileCenter,
    },
    routes: {
      left: routesRect.left,
      width: routesRect.width,
      center: routesCenter,
    },
    delta,
    routesMarginLeft: getComputedStyle(routes).marginLeft,
    routesMarginRight: getComputedStyle(routes).marginRight,
    innerWidth: document
      .querySelector(".launcher-inline-routes-panel__inner")
      ?.getBoundingClientRect().width,
    panelWidth: document
      .querySelector(".launcher-inline-routes-panel--launcher.is-expanded")
      ?.getBoundingClientRect().width,
  };
});

await browser.close();

if (metrics.error) {
  console.error(`FAIL: ${metrics.error}`);
  process.exit(1);
}

const ok = metrics.delta <= MAX_CENTER_DELTA_PX;

console.log("Launcher routes alignment:");
console.log(JSON.stringify(metrics, null, 2));
console.log(
  ok
    ? `PASS: submenu centralizado (delta=${metrics.delta.toFixed(2)}px)`
    : `FAIL: submenu descentralizado (delta=${metrics.delta.toFixed(2)}px > ${MAX_CENTER_DELTA_PX}px)`,
);

process.exit(ok ? 0 : 1);
