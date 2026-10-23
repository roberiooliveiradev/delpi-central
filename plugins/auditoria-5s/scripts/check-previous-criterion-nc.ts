/**
 * Smoke estrutural: aviso de NC da auditoria anterior no fill.
 * npm run check:previous-criterion-nc
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "src");

function read(relative: string): string {
  return readFileSync(join(root, relative), "utf8");
}

const banner = read("components/PreviousCriterionNcBanner.tsx");
assert.match(
  banner,
  /Na auditoria anterior, foi identificada uma não conformidade neste critério\./,
);
assert.match(banner, /Visualizar detalhes/);
assert.match(banner, /a5s-previous-nc-banner/);

const modal = read("components/PreviousCriterionNcModal.tsx");
assert.match(modal, /Voltar à avaliação/);
assert.match(modal, /Situação/);
assert.match(modal, /Observações da avaliação/);

const page = read("pages/Audit5sPage.tsx");
assert.match(page, /previousNcByCode\[criterion\.code\.trim\(\)\.toUpperCase\(\)\]/);
assert.match(page, /fetchPreviousCriterionNonconformities/);
assert.match(page, /PreviousCriterionNcBanner/);
assert.match(page, /previousNcLoadError/);
assert.match(
  page,
  /Não foi possível verificar NCs da auditoria anterior/,
);

const api = read("api/audit5sApi.ts");
assert.match(api, /previous-criterion-nonconformities/);

console.log("check:previous-criterion-nc OK");
