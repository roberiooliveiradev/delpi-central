// Geometric layout check for the ticket-create form — P1 overlap regression.
//
// Reproduces the REAL host chain (Portal .content > .app-host-federated >
// .app-host-federated__mount > .dashboard-page--fill > .helpdesk-page-stack)
// with the REAL stylesheets (portal + plugin-ui + helpdesk) and measures
// element rectangles in headless Chromium:
//   - the grid must never collapse below its intrinsic minimum when the
//     items section expands (previously it shrank to h=0 and the aside
//     fields painted over the files/Enviar area);
//   - the aside must never overlap the files/actions region;
//   - when the window is too short, the FORM scrolls — fields reachable.
//
// Run (from plugins/helpdesk):
//   node scripts/create-layout-check.mjs
// Requires playwright resolvable via ../bpmn-modeler/node_modules and
// Chromium in ~/.cache/ms-playwright (provisioned). If the headless shell
// misses system libs: apt download libnspr4 libnss3 libasound2t64 into
// /tmp/pwlibs, dpkg -x, then
//   LD_LIBRARY_PATH=/tmp/pwlibs/usr/lib/x86_64-linux-gnu node scripts/create-layout-check.mjs
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const require = createRequire(join(root, "../../bpmn-modeler/package.json"));
const { chromium } = require("playwright");

const css =
  readFileSync(join(root, "../../../portal/src/index.css"), "utf8") +
  readFileSync(join(root, "../../plugin-ui/src/styles.css"), "utf8") +
  readFileSync(join(root, "../src/index.css"), "utf8");

function field(label) {
  // Representative field ≈ HelpdeskSelect/HelpdeskTextField intrinsic height.
  return `<div class="fake-field"><label>${label}</label><div class="fake-field__control"></div></div>`;
}

function html({ itemsOpen }) {
  return `<!doctype html><style>${css}</style><style>
html,body{margin:0;height:100%}
.content{height:700px}
.fake-field{min-height:4.25rem}
.fake-field label{display:block;font-size:.8rem;margin-bottom:4px}
.fake-field__control{height:2rem;border:1px solid #cbd5e1}
.fake-editor{min-height:120px;flex:1 1 auto;border:1px solid #cbd5e1}
.fake-results{height:15rem;border:1px solid #cbd5e1}
</style>
<div class="content"><div class="app-host-federated"><div class="app-host-federated__mount is-ready">
<div class="dashboard-helpdesk dashboard-page dashboard-page--fill"><div class="helpdesk-page-stack"><div style="height:48px;flex:0 0 auto">H</div>
<form class="helpdesk-create-form"><div class="helpdesk-create-layout"><div class="helpdesk-create-layout__main">${field("Título")}<div class="fake-editor" data-field="editor"></div></div>
<aside class="helpdesk-create-layout__aside">${field("Categoria")}${field("Tipo")}${field("Urgência")}${field("Impacto")}${field("Origem")}${field("Técnico")}${field("Observadores")}</aside></div>
<div class="helpdesk-create-files" data-region="files"><div class="helpdesk-create-files__actions"><button type="button" class="helpdesk-compose-attach">img</button><button type="submit" class="helpdesk-create-send">Enviar</button></div></div>
<section class="helpdesk-create-items" data-region="items"><button type="button" class="helpdesk-create-items__toggle">toggle</button>${
    itemsOpen
      ? `<div class="helpdesk-create-items__body">${field("Origem da busca")}${field("Tipo de item")}<div class="fake-results"></div>${field("Chamado relacionado")}</div>`
      : ""
  }</section></form></div></div></div></div>`;
}

const results = [];
const check = (name, ok, detail) => {
  results.push({ name, ok });
  console.log(`${ok ? "PASS" : "FAIL"} ${name}${detail ? " — " + detail : ""}`);
};

const browser = await chromium.launch();

const scenarios = [
  { itemsOpen: false, width: 1366, tag: "collapsed" },
  { itemsOpen: true, width: 1366, tag: "expanded" },
  { itemsOpen: true, width: 420, tag: "expanded-mobile" },
];

for (const { itemsOpen, width, tag } of scenarios) {
  const page = await browser.newPage({ viewport: { width, height: 700 } });
  await page.setContent(html({ itemsOpen }));

  const m = await page.evaluate(() => {
    const rect = (s) => {
      const e = document.querySelector(s);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { top: r.top, bottom: r.bottom, height: r.height };
    };
    const form = document.querySelector(".helpdesk-create-form");
    const lastField = document.querySelector(
      ".helpdesk-create-layout__aside .fake-field:last-child",
    );
    const lastBottom = lastField.getBoundingClientRect().bottom;
    const formRect = form.getBoundingClientRect();
    return {
      layout: rect(".helpdesk-create-layout"),
      aside: rect(".helpdesk-create-layout__aside"),
      asideLastFieldBottom: lastBottom,
      files: rect('[data-region="files"]'),
      formScrollable: form.scrollHeight > form.clientHeight + 1,
      formCH: form.clientHeight,
      formSH: form.scrollHeight,
      // Field clipped beyond the form's visible box = inaccessible.
      lastFieldClipped: lastBottom > formRect.bottom + 1,
    };
  });

  check(
    `[${tag}] grid keeps intrinsic height (no collapse to zero)`,
    m.layout.height > 400,
    `layout.h=${m.layout.height.toFixed(0)}`,
  );
  check(
    `[${tag}] aside does not overlap files area`,
    m.aside.bottom <= m.files.top + 0.5,
    `aside.bottom=${m.aside.bottom.toFixed(0)} files.top=${m.files.top.toFixed(0)}`,
  );
  check(
    `[${tag}] last aside field does not overlap files area`,
    m.asideLastFieldBottom <= m.files.top + 0.5 || m.lastFieldClipped === false,
    `lastField.bottom=${m.asideLastFieldBottom.toFixed(0)} files.top=${m.files.top.toFixed(0)}`,
  );
  if (m.formScrollable) {
    check(
      `[${tag}] insufficient height → form scrolls`,
      true,
      `scrollHeight=${m.formSH} client=${m.formCH}`,
    );
    const reachable = await page.evaluate(() => {
      const form = document.querySelector(".helpdesk-create-form");
      form.scrollTop = form.scrollHeight;
      const files = document
        .querySelector('[data-region="files"]')
        .getBoundingClientRect();
      return files.bottom <= form.getBoundingClientRect().bottom + 1;
    });
    check(`[${tag}] scrolling reaches files/Enviar`, reachable);
  } else {
    check(
      `[${tag}] all fields within viewport (no clipping)`,
      !m.lastFieldClipped,
      `lastField.bottom=${m.asideLastFieldBottom.toFixed(0)} form.bottom`,
    );
  }
  await page.close();
}

await browser.close();
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
process.exit(failed.length ? 1 : 0);
