import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("Account audit timeline Conta", () => {
  it("Contatos inclui AccountAuditSection e API audit", () => {
    const page = readFileSync(
      join(src, "features/customers/pages/CustomerDetailPage.tsx"),
      "utf8",
    );
    assert.match(page, /AccountAuditSection/);
    assert.match(page, /contactsRefreshKey/);

    const api = readFileSync(
      join(src, "api/customerAccountAuditApi.ts"),
      "utf8",
    );
    assert.match(api, /\/customers\/.*\/audit/);
  });
});
