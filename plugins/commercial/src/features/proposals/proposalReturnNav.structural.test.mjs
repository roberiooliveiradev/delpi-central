#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("Proposal detail returnTo (E5.S3)", () => {
  it("detalhe resolve returnTo e lista propaga returnNav", () => {
    const detail = readFileSync(
      join(src, "features/proposals/ProposalDetailPage.tsx"),
      "utf8",
    );
    assert.match(detail, /resolvePagePathBack/);
    assert.match(detail, /back\.href/);
    assert.match(detail, /back\.label/);

    const table = readFileSync(
      join(src, "features/proposals/ProposalsDocumentsTable.tsx"),
      "utf8",
    );
    assert.match(table, /returnNav/);
    assert.match(table, /currentLocationAsReturnTo/);
  });
});
