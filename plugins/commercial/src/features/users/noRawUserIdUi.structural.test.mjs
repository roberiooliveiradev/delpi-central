#!/usr/bin/env node
/**
 * Gate: nunca renderizar user_id / UUID cru como texto de UI no MFE commercial.
 * Paths/API/keys internas podem usar ids — proibição é de label/render ao usuário.
 */
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const srcRoot = join(dirname(fileURLToPath(import.meta.url)), "../..");

function walk(dir, acc = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === "dist") continue;
      walk(full, acc);
    } else if (/\.(tsx|ts|json)$/.test(entry.name) && !entry.name.includes(".test.")) {
      acc.push(full);
    }
  }
  return acc;
}

describe("Privacidade UI — zero user_id cru (E12.S2)", () => {
  it("não há label/copy «ID do usuário» nem render de profile.user_id na UI", () => {
    const profile = readFileSync(join(srcRoot, "features/users/UserProfilePage.tsx"), "utf8");
    assert.doesNotMatch(profile, /userIdLabel/);
    assert.doesNotMatch(profile, /ID do usuário/);
    assert.doesNotMatch(
      profile,
      /USER_ACCESS_COPY\.userIdLabel|ID do usuário:\s*\{?\s*profile\.user_id/,
    );
    assert.doesNotMatch(profile, /profile\.name\s*\|\|\s*profile\.user_id/);
    assert.match(profile, /directoryUserLabelOrFallback/);

    const copy = JSON.parse(
      readFileSync(join(srcRoot, "content/userAccess.json"), "utf8"),
    );
    assert.equal(copy.copy.userIdLabel, undefined);
  });

  it("fallbacks de Equipe/OrgFlow não usam user_id como texto", () => {
    const team = readFileSync(
      join(srcRoot, "features/administration/AdministrationTeamPage.tsx"),
      "utf8",
    );
    assert.doesNotMatch(team, /row\.name\s*\|\|\s*row\.user_id/);
    assert.match(team, /directoryUserLabelOrFallback/);

    const orgFlow = readFileSync(join(srcRoot, "utils/commercialTeamOrgFlow.ts"), "utf8");
    assert.doesNotMatch(orgFlow, /\|\|\s*person\.user_id/);
    assert.match(orgFlow, /directoryUserLabelOrFallback/);
  });

  it("nenhum TSX/JSON de content exibe o rótulo proibido", () => {
    const forbidden = /ID do usuário|userIdLabel/;
    const offenders = [];
    for (const file of walk(srcRoot)) {
      const text = readFileSync(file, "utf8");
      if (forbidden.test(text)) {
        offenders.push(relative(srcRoot, file));
      }
    }
    assert.deepEqual(offenders, [], `rótulo proibido em: ${offenders.join(", ")}`);
  });
});
