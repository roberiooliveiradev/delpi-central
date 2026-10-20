#!/usr/bin/env node
/**
 * Boundary MFE → BFF: o navegador só fala com /apps/controllership-finance-api.
 * Proibido: chamadas diretas a core-api, api-delpi ou outras BFFs de irmãos.
 */
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const src = join(dirname(fileURLToPath(import.meta.url)), "..");

function* walk(dir) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      yield* walk(full);
    } else if (/\.(ts|tsx)$/.test(entry) && !/\.test\.(ts|tsx)$/.test(entry)) {
      yield full;
    }
  }
}

const sources = [...walk(src)].map((f) => ({
  file: f,
  code: readFileSync(f, "utf8"),
}));

const FORBIDDEN_ORIGINS = [
  /\/apps\/api-delpi\b/,
  /\/apps\/core-api\b/,
  /\/api-delpi\//,
  /\/core-api\//,
  /\/apps\/(commercial|financial|requests|strategic-indicators|helpdesk|travel-expenses|transformometro|cipa|comite-etica-conduta|customer-experience|maintenance|production-control|purchase-requests|supplies|tv-dashboard|delia|bpmn)-api\b/,
];

describe("boundary MFE → BFF", () => {
  it("toda chamada fetch passa pelo httpClient da BFF do produto", () => {
    const httpClient = sources.find((s) => s.file.endsWith("api/httpClient.ts"));
    assert.ok(httpClient, "httpClient ausente");
    assert.match(httpClient.code, /CONTROLLERSHIP_FINANCE_API_BASE = "\/apps\/controllership-finance-api"/);
    assert.match(httpClient.code, /"X-Delpi-Caller-App": DELPI_CALLER_APP/);
    assert.match(httpClient.code, /DELPI_CALLER_APP = "controllership-finance"/);
    assert.match(httpClient.code, /Authorization = `Bearer \$\{token\}`/);
  });

  it("nenhum módulo chama fetch/axios fora do httpClient", () => {
    for (const { file, code } of sources) {
      if (file.endsWith("api/httpClient.ts")) continue;
      assert.doesNotMatch(code, /\bfetch\s*\(/, `fetch fora do httpClient: ${file}`);
      assert.doesNotMatch(code, /\baxios\b/, `axios fora do httpClient: ${file}`);
    }
  });

  it("nenhuma origem proibida é referenciada (Core, api-delpi, BFFs irmãs)", () => {
    for (const { file, code } of sources) {
      for (const pattern of FORBIDDEN_ORIGINS) {
        assert.doesNotMatch(
          code,
          pattern,
          `origem proibida em ${file}: ${pattern}`,
        );
      }
    }
  });

  it("viewer-context é o único contrato consumido", () => {
    const api = sources.find((s) => s.file.endsWith("api/viewerContextApi.ts"));
    assert.ok(api, "viewerContextApi ausente");
    assert.match(api.code, /cfApiUrl\("\/viewer-context"\)/);
    assert.doesNotMatch(api.code, /permissions.*jwt|decode.*token/i);
  });
});
