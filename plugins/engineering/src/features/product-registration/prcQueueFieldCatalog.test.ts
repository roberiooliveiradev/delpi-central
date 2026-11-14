import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import type { PrcRequestSummary } from "./api/productRegistrationApi";
import { PRC_COPY, PRC_STATUS_LABELS, PRC_TYPE_LABELS } from "./prcCopy";
import {
  PRC_QUEUE_COLUMN_CATALOG,
  PRC_QUEUE_FIELD_KEYS,
  PRC_QUEUE_FIELD_LABELS,
  formatPrcKanbanColumnCountMeta,
  formatPrcQueueCreatedAt,
  getPrcQueueFieldPlainText,
  resolveVisiblePrcQueueFields,
  resolvePrcQueueFieldOrder,
} from "./prcQueueFieldCatalog";
import { buildPrcCardColumns } from "./components/PrcRequestCard";

const here = dirname(fileURLToPath(import.meta.url));

const SAMPLE: PrcRequestSummary = {
  id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  requestType: "create",
  status: "submitted",
  requester: { subject: "user-1", displayName: "Ana Silva" },
  source: "portal",
  createdAt: "2026-11-14T13:30:00.000Z",
  assignedTo: null,
  assignedToDisplayName: null,
  officialCode: null,
  caseVersion: 1,
};

const SAMPLE_ASSIGNED: PrcRequestSummary = {
  ...SAMPLE,
  id: "11111111-2222-3333-4444-555555555555",
  requestType: "update",
  status: "in_progress",
  officialCode: "PROD-99",
  assignedTo: "eng-2",
  assignedToDisplayName: "Bruno Costa",
  requester: { subject: "user-2", displayName: "Carla Dias" },
};

describe("prcQueueFieldCatalog — paridade informacional", () => {
  it("catálogo padrão tem os sete campos oficiais com rótulos pt-BR", () => {
    expect(PRC_QUEUE_FIELD_KEYS).toEqual([
      "id",
      "type",
      "requester",
      "officialCode",
      "createdAt",
      "status",
      "assignedTo",
    ]);
    expect(PRC_QUEUE_COLUMN_CATALOG.map((c) => c.label)).toEqual([
      "Nº",
      "Tipo",
      "Solicitante",
      "Código oficial",
      "Abertura",
      "Status",
      "Responsável",
    ]);
    expect(PRC_QUEUE_FIELD_LABELS.status).toBe("Status");
  });

  it("textos padrão: tipo/status pt-BR, código ausente, responsável não atribuído", () => {
    expect(getPrcQueueFieldPlainText(SAMPLE, "type")).toBe(
      PRC_TYPE_LABELS.create,
    );
    expect(getPrcQueueFieldPlainText(SAMPLE, "status")).toBe(
      PRC_STATUS_LABELS.submitted,
    );
    expect(getPrcQueueFieldPlainText(SAMPLE, "officialCode")).toBe(
      PRC_COPY.awaitingCode,
    );
    expect(getPrcQueueFieldPlainText(SAMPLE, "assignedTo")).toBe(
      PRC_COPY.unassigned,
    );
    expect(getPrcQueueFieldPlainText(SAMPLE, "requester")).toBe("Ana Silva");
    expect(getPrcQueueFieldPlainText(SAMPLE, "id")).toBe("#a1b2c3d4");
  });

  it("código oficial e responsável preenchidos", () => {
    expect(getPrcQueueFieldPlainText(SAMPLE_ASSIGNED, "officialCode")).toBe(
      "PROD-99",
    );
    expect(getPrcQueueFieldPlainText(SAMPLE_ASSIGNED, "assignedTo")).toBe(
      "Bruno Costa",
    );
    expect(getPrcQueueFieldPlainText(SAMPLE_ASSIGNED, "type")).toBe(
      PRC_TYPE_LABELS.update,
    );
  });

  it("datas em pt-BR", () => {
    const formatted = formatPrcQueueCreatedAt(SAMPLE.createdAt);
    expect(formatted).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    expect(getPrcQueueFieldPlainText(SAMPLE, "createdAt")).toBe(formatted);
  });

  it("ocultar campo remove da lista visível; identidade pode ser forçada", () => {
    const visibility = Object.fromEntries(
      PRC_QUEUE_FIELD_KEYS.map((k) => [k, true]),
    );
    visibility.createdAt = false;
    visibility.id = false;
    const withoutIdentity = resolveVisiblePrcQueueFields({ visibility });
    expect(withoutIdentity).not.toContain("createdAt");
    expect(withoutIdentity).not.toContain("id");
    const withIdentity = resolveVisiblePrcQueueFields({
      visibility,
      forceIdentity: true,
    });
    expect(withIdentity[0]).toBe("id");
    expect(withIdentity).not.toContain("createdAt");
  });

  it("omitStatus remove Status (Kanban)", () => {
    const visibility = Object.fromEntries(
      PRC_QUEUE_FIELD_KEYS.map((k) => [k, true]),
    );
    const keys = resolveVisiblePrcQueueFields({
      visibility,
      omitStatus: true,
      forceIdentity: true,
    });
    expect(keys).not.toContain("status");
    expect(keys).toContain("id");
  });

  it("reordenar preferência é respeitada", () => {
    expect(
      resolvePrcQueueFieldOrder(["status", "id", "ghost", "type"]),
    ).toEqual([
      "status",
      "id",
      "type",
      "requester",
      "officialCode",
      "createdAt",
      "assignedTo",
    ]);
  });

  it("contagem Kanban distingue total do escopo e exibidas na página", () => {
    expect(
      formatPrcKanbanColumnCountMeta({
        status: "completed",
        totalInScope: 10,
        displayedOnPage: 6,
      }),
    ).toBe("10 no total · 6 nesta página");
    expect(
      formatPrcKanbanColumnCountMeta({
        status: "submitted",
        totalInScope: 0,
        displayedOnPage: 0,
      }),
    ).toBe("0 no total · 0 nesta página");
  });
});

describe("buildPrcCardColumns — identidade e omit", () => {
  const all = PRC_QUEUE_FIELD_KEYS.map((key) => ({
    key,
    header: PRC_QUEUE_FIELD_LABELS[key],
    render: () => key,
  }));

  it("força id à frente mesmo se oculto nas visíveis", () => {
    const visible = all.filter((c) => c.key === "type" || c.key === "status");
    const built = buildPrcCardColumns(all, visible);
    expect(built.map((c) => c.key)).toEqual(["id", "type", "status"]);
  });

  it("omitKeys remove status no Kanban", () => {
    const built = buildPrcCardColumns(all, all, { omitKeys: ["status"] });
    expect(built.map((c) => c.key)).not.toContain("status");
    expect(built[0]?.key).toBe("id");
  });
});

describe("PrcQueuePage / PrcRequestCard — wiring §47", () => {
  it("página usa PrcRequestCard nos modos Cards e Kanban", () => {
    const page = readFileSync(join(here, "pages/PrcQueuePage.tsx"), "utf8");
    expect(page).toMatch(/<PrcRequestCard/);
    expect(page).toMatch(/layout === "cards"/);
    expect(page).toMatch(/layout === "board"/);
    expect(page).toMatch(/buildPrcCardColumns/);
    expect(page).toMatch(/omitKeys:\s*\["status"\]/);
    expect(page).toMatch(/formatPrcKanbanColumnCountMeta/);
    expect(page).toMatch(/COLUMN_PREFERENCES_KEY/);
    expect(page).toMatch(/engineering:prc:requests:columns/);
    /* Menu Colunas sem gate layout === "table" */
    expect(page).not.toMatch(
      /layout === "table" \? \(\s*<TableColumnVisibilityMenu/,
    );
    expect(page).toMatch(/<TableColumnVisibilityMenu/);
    expect(page).toMatch(/PRC_QUEUE_COLUMN_CATALOG/);
    /* Sem EngineeringInteractiveDataCard inline (só via PrcRequestCard) */
    expect(page).not.toMatch(/EngineeringInteractiveDataCard/);
    expect(page).toMatch(/navigatePrc\(PRC_PATHS\.detail/);
  });

  it("PrcRequestCard reutiliza renders das colunas e openHint pt-BR", () => {
    const card = readFileSync(
      join(here, "components/PrcRequestCard.tsx"),
      "utf8",
    );
    expect(card).toMatch(/column\.render\(row\)/);
    expect(card).toMatch(/PRC_COPY\.openRequest/);
    expect(card).toMatch(/EngineeringInteractiveDataCard/);
    expect(card).toMatch(/present:\s*true/);
    expect(card).not.toMatch(/drag/i);
  });

  it("não há drag-and-drop de workflow na fila", () => {
    const page = readFileSync(join(here, "pages/PrcQueuePage.tsx"), "utf8");
    expect(page.toLowerCase()).not.toMatch(/onDrag|draggable|dnd-kit/);
  });
});
