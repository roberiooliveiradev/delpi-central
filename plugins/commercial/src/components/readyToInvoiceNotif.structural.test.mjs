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

  it("content JSON declares billing lists and deep link without forced board view", () => {
    const raw = readFileSync(
      join(apiRoot, "commercial_app/content/pt-BR/ready_to_invoice_notification.json"),
      "utf8",
    );
    const json = JSON.parse(raw);
    const deepLink = json.deepLinkPath || json.boardDeepLinkPath;
    assert.equal(typeof deepLink, "string");
    assert.ok(!/view=board/.test(deepLink));
    assert.match(deepLink, /ready_to_invoice|open-orders/);
    assert.ok(Array.isArray(json.billingUserIds));
    assert.ok(Array.isArray(json.billingPermissionCodes));
  });

  it("MFE board deep link helper supports ready_to_invoice", () => {
    const src = readFileSync(join(root, "utils/openOrdersDeepLink.ts"), "utf8");
    assert.match(src, /buildOpenOrdersBoardHref/);
    assert.match(src, /ready_to_invoice|stage/);
  });

  it("MFE realtime toast wires orders.ready_to_invoice", () => {
    const realtime = readFileSync(join(root, "constants/realtime.ts"), "utf8");
    assert.match(realtime, /orders\.ready_to_invoice/);
    assert.match(realtime, /resolveReadyToInvoiceNotification/);
    const provider = readFileSync(
      join(root, "app/CommercialRealtimeProvider.tsx"),
      "utf8",
    );
    assert.match(provider, /subscribeReadyToInvoice/);
    assert.match(provider, /resolveReadyToInvoiceNotification/);
  });
});
