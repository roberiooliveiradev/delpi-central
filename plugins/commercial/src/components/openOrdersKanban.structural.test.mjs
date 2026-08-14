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
  });

  it("KanbanBoardView agrupa por kanbanStage do BFF", () => {
    const src = readFileSync(join(root, "components/OpenOrdersKanbanBoard.tsx"), "utf8");
    assert.match(src, /kanbanStage/);
    assert.match(src, /CommercialKanbanBoard/);
    assert.doesNotMatch(src, /api-delpi|API_DELPI/);
    assert.doesNotMatch(src, /\.cm-kanban-board\s*\{/);
  });

  it("commercialUi exporta CommercialKanbanBoard", () => {
    const src = readFileSync(join(root, "app/commercialUi.ts"), "utf8");
    assert.match(src, /CommercialKanbanBoard\s*=\s*createDashboardKanbanBoard/);
  });
});
