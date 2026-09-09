import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  auditSource,
  collectAdminHelpCoverageGaps,
  gapKey,
  loadAllowlist,
  partitionAgainstAllowlist,
} from "./auditAdminHelpCoverage.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(here, "..");
const allowlistPath = join(here, "adminHelpCoverage.allowlist.json");

describe("admin help coverage", () => {
  it("não deixa tela admin/studio sem hint canônico fora da allowlist", () => {
    const gaps = collectAdminHelpCoverageGaps(srcRoot);
    const allowlist = loadAllowlist(allowlistPath);
    const { unexpected, staleAllowlist } = partitionAgainstAllowlist(gaps, allowlist);

    expect(unexpected.map(gapKey), unexpected.map(gapKey).join("\n")).toEqual([]);
    expect(staleAllowlist.map(gapKey), staleAllowlist.map(gapKey).join("\n")).toEqual([]);
  });

  it("detecta ChatAdminNative*Field sem hint e AdminTabHeader sem helpHint", () => {
    const missingField = auditSource(
      "fixture.tsx",
      `<ChatAdminNativeTextField id="x" label="Buscar" value="" onChange={() => undefined} />`,
    );
    expect(missingField.some((gap) => gap.kind === "native-field")).toBe(true);

    const coveredField = auditSource(
      "fixture.tsx",
      `<ChatAdminNativeTextField id="x" label="Buscar" hint={ADMIN_HELP.fields.documents.search} value="" onChange={() => undefined} />`,
    );
    expect(coveredField.filter((gap) => gap.kind === "native-field")).toEqual([]);

    const missingHeader = auditSource(
      "fixture.tsx",
      `<AdminTabHeader title="Painel" description="Resumo" />`,
    );
    expect(missingHeader.some((gap) => gap.kind === "tab-header")).toBe(true);
  });
});
