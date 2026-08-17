#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const apiRoot = join(root, "../../../commercial-api");

describe("ready_to_invoice notification wiring", () => {
  it("job route exists under integrations/jobs", () => {
    const src = readFileSync(
      join(apiRoot, "commercial_app/interface/http/routes/integration_jobs_routes.py"),
      "utf8",
    );
    assert.match(src, /ready-to-invoice-scan/);
    assert.match(src, /COMMERCIAL_MANAGE_PERMISSIONS/);
  });

  it("content JSON declares billing lists and board deep link", () => {
    const raw = readFileSync(
      join(apiRoot, "commercial_app/content/pt-BR/ready_to_invoice_notification.json"),
      "utf8",
    );
    const json = JSON.parse(raw);
    assert.equal(typeof json.boardDeepLinkPath, "string");
    assert.match(json.boardDeepLinkPath, /view=board/);
    assert.match(json.boardDeepLinkPath, /ready_to_invoice/);
    assert.ok(Array.isArray(json.billingUserIds));
    assert.ok(Array.isArray(json.billingPermissionCodes));
  });

  it("MFE board deep link helper supports ready_to_invoice", () => {
    const src = readFileSync(join(root, "utils/openOrdersDeepLink.ts"), "utf8");
    assert.match(src, /buildOpenOrdersBoardHref/);
    assert.match(src, /ready_to_invoice|stage/);
  });
});
