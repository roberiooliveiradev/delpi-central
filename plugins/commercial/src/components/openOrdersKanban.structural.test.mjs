#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

describe("openOrdersKanban structural", () => {
  it("OpenOrdersTable expõe opção Board e consome KanbanBoardView", () => {
    const src = readFileSync(join(root, "components/OpenOrdersTable.tsx"), "utf8");
    assert.match(src, /value:\s*"board"/);
    assert.match(src, /OpenOrdersKanbanBoardView/);
    assert.match(src, /parseOpenOrdersListUrlState/);
    assert.match(src, /useRecentlyClosedOrdersTotvs/);
    assert.match(src, /completedRows=\{closedOrders\.items\}/);
    assert.doesNotMatch(src, /api-delpi|API_DELPI/);
  });

  it("KanbanBoardView agrupa por kanbanStage do BFF", () => {
    const src = readFileSync(join(root, "components/OpenOrdersKanbanBoard.tsx"), "utf8");
    assert.match(src, /kanbanStage/);
    assert.match(src, /CommercialKanbanBoard/);
    assert.match(src, /completedRows/);
    assert.doesNotMatch(src, /api-delpi|API_DELPI/);
    assert.doesNotMatch(src, /\.cm-kanban-board\s*\{/);
  });

  it("API e hook de concluídos usam só BFF commercial", () => {
    const api = readFileSync(join(root, "api/openOrdersTotvsApi.ts"), "utf8");
    assert.match(api, /getRecentlyClosedOrdersTotvs/);
    assert.match(api, /\/open-orders\/recently-closed/);
    assert.doesNotMatch(api, /api-delpi|API_DELPI|totvs-recently-closed/);
    const hook = readFileSync(join(root, "hooks/useRecentlyClosedOrdersTotvs.ts"), "utf8");
    assert.match(hook, /getRecentlyClosedOrdersTotvs/);
  });

  it("commercialUi exporta CommercialKanbanBoard", () => {
    const src = readFileSync(join(root, "app/commercialUi.ts"), "utf8");
    assert.match(src, /CommercialKanbanBoard\s*=\s*createDashboardKanbanBoard/);
  });
});
