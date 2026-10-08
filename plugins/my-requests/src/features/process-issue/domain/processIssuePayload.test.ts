import { describe, expect, it } from "vitest";

import {
  formatProcessIssueQty,
  formatProcessIssueSchedule,
  parseProcessIssuePayload,
  processIssueLabel,
  PROCESS_ISSUE_LABELS,
} from "./processIssuePayload";

const COMPLETE_PAYLOAD = {
  source: "operator_cockpit",
  reportedAt: "2026-03-12T13:45:00+00:00",
  issue: {
    code: "tool_not_linked",
    reportedToolCode: "F12345",
    reportedMaterialCode: "10099999",
    note: "Ferramenta utilizada na montagem não consta na operação.",
  },
  operator: { code: "001234", name: "João da Silva" },
  operation: {
    productionOrder: "24640401002",
    operationCode: "03",
    description: "MONTAGEM",
    reportedWorkCenter: "CT-63",
    workCenterName: "Montagem 03",
    productCode: "10045678",
    productDescription: "PRODUTO INTERMEDIÁRIO",
    unit: "PC",
    paProductCode: "90264238",
    paProductDescription: "CONJUNTO FINAL",
    toolSnapshot: "F10000",
    resource: "BANC-07",
    plannedQty: 100,
    pendingQty: 50,
    operationPendingQty: 25,
    scheduledDate: "2026-03-15",
    scheduledStartTime: "07:30:00",
    scheduledEndDate: "2026-03-16",
    scheduledEndTime: "17:00:00",
    dueDate: "2026-03-20",
  },
  materialsSnapshotAvailable: true,
  materials: [
    {
      productCode: "10081234",
      description: "TERMINAL",
      unit: "PC",
      originalQty: 10,
      openQty: 4,
      consumedQty: 6,
    },
    { productCode: "10085678", description: "CABO", unit: "M" },
  ],
};

describe("processIssueLabel", () => {
  it("mapeia os seis códigos canônicos", () => {
    expect(Object.keys(PROCESS_ISSUE_LABELS)).toHaveLength(6);
    expect(processIssueLabel("work_center_incompatible")).toBe(
      "CT / posto não adequado",
    );
    expect(processIssueLabel("machine_limitation")).toBe(
      "Limitação da máquina ou bancada",
    );
    expect(processIssueLabel("tool_not_linked")).toBe(
      "Ferramenta não informada ou não vinculada",
    );
    expect(processIssueLabel("material_not_linked")).toBe(
      "Matéria-prima não vinculada à operação",
    );
    expect(processIssueLabel("process_information_missing")).toBe(
      "Informação de processo incompleta",
    );
    expect(processIssueLabel("other")).toBe("Outro problema de processo");
  });

  it("faz fallback seguro para código desconhecido ou ausente", () => {
    expect(processIssueLabel("legacy_code")).toBe("Problema de processo");
    expect(processIssueLabel(null)).toBe("Problema de processo");
    expect(processIssueLabel(undefined)).toBe("Problema de processo");
    expect(processIssueLabel("  ")).toBe("Problema de processo");
  });
});

describe("parseProcessIssuePayload", () => {
  it("normaliza payload completo", () => {
    const view = parseProcessIssuePayload(COMPLETE_PAYLOAD);

    expect(view.source).toBe("operator_cockpit");
    expect(view.reportedAt).toBe("2026-03-12T13:45:00+00:00");
    expect(view.issueCode).toBe("tool_not_linked");
    expect(view.issueLabel).toBe("Ferramenta não informada ou não vinculada");
    expect(view.reportedToolCode).toBe("F12345");
    expect(view.reportedMaterialCode).toBe("10099999");
    expect(view.note).toContain("não consta na operação");
    expect(view.operatorCode).toBe("001234");
    expect(view.operatorName).toBe("João da Silva");
    expect(view.productionOrder).toBe("24640401002");
    expect(view.operationCode).toBe("03");
    expect(view.operationDescription).toBe("MONTAGEM");
    expect(view.reportedWorkCenter).toBe("CT-63");
    expect(view.workCenterName).toBe("Montagem 03");
    expect(view.productCode).toBe("10045678");
    expect(view.productDescription).toBe("PRODUTO INTERMEDIÁRIO");
    expect(view.unit).toBe("PC");
    expect(view.paProductCode).toBe("90264238");
    expect(view.paProductDescription).toBe("CONJUNTO FINAL");
    expect(view.toolSnapshot).toBe("F10000");
    expect(view.resource).toBe("BANC-07");
    expect(view.plannedQty).toBe(100);
    expect(view.pendingQty).toBe(50);
    expect(view.operationPendingQty).toBe(25);
    expect(view.scheduledDate).toBe("2026-03-15");
    expect(view.dueDate).toBe("2026-03-20");
    expect(view.materialsSnapshotAvailable).toBe(true);
    expect(view.materials).toHaveLength(2);
    expect(view.materials[0]).toMatchObject({
      productCode: "10081234",
      originalQty: 10,
      openQty: 4,
      consumedQty: 6,
    });
  });

  it("não quebra com payload ausente ou não-objeto", () => {
    for (const payload of [null, undefined, {}, "x", 42, []]) {
      const view = parseProcessIssuePayload(payload);
      expect(view.issueCode).toBeNull();
      expect(view.issueLabel).toBe("Problema de processo");
      expect(view.paProductCode).toBeNull();
      expect(view.materialsSnapshotAvailable).toBe(false);
      expect(view.materials).toEqual([]);
    }
  });

  it("trata campos opcionais ausentes", () => {
    const view = parseProcessIssuePayload({
      source: "operator_cockpit",
      reportedAt: "2026-03-12T10:00:00Z",
      issue: { code: "other" },
      operator: { code: "9" },
      operation: {
        productionOrder: "1",
        operationCode: "02",
        reportedWorkCenter: "CT-01",
      },
    });
    expect(view.reportedToolCode).toBeNull();
    expect(view.reportedMaterialCode).toBeNull();
    expect(view.note).toBeNull();
    expect(view.paProductCode).toBeNull();
    expect(view.toolSnapshot).toBeNull();
    expect(view.operationDescription).toBeNull();
  });

  it("distingue ferramenta do snapshot da informada pelo operador", () => {
    const view = parseProcessIssuePayload(COMPLETE_PAYLOAD);
    expect(view.toolSnapshot).toBe("F10000");
    expect(view.reportedToolCode).toBe("F12345");
    expect(view.toolSnapshot).not.toBe(view.reportedToolCode);
  });

  it("materialsSnapshotAvailable=false preserva flag mesmo com lista presente", () => {
    const view = parseProcessIssuePayload({
      ...COMPLETE_PAYLOAD,
      materialsSnapshotAvailable: false,
      materials: [{ productCode: "X" }],
    });
    expect(view.materialsSnapshotAvailable).toBe(false);
    // ainda normaliza a lista (render decide o que mostrar)
    expect(view.materials).toHaveLength(1);
  });

  it("snapshot disponível com lista vazia", () => {
    const view = parseProcessIssuePayload({
      ...COMPLETE_PAYLOAD,
      materialsSnapshotAvailable: true,
      materials: [],
    });
    expect(view.materialsSnapshotAvailable).toBe(true);
    expect(view.materials).toEqual([]);
  });

  it("quantidades zero permanecem zero (não viram ausente)", () => {
    const view = parseProcessIssuePayload({
      ...COMPLETE_PAYLOAD,
      operation: {
        ...COMPLETE_PAYLOAD.operation,
        plannedQty: 0,
        pendingQty: 0,
        operationPendingQty: 0,
      },
    });
    expect(view.plannedQty).toBe(0);
    expect(view.pendingQty).toBe(0);
    expect(view.operationPendingQty).toBe(0);
  });

  it("material sem quantidade não quebra", () => {
    const view = parseProcessIssuePayload(COMPLETE_PAYLOAD);
    const semQty = view.materials[1];
    expect(semQty.productCode).toBe("10085678");
    expect(semQty.originalQty).toBeNull();
  });
});

describe("formatProcessIssueQty", () => {
  it("formata números pt-BR e retorna null para ausente", () => {
    expect(formatProcessIssueQty(1000)).toBe("1.000");
    expect(formatProcessIssueQty(0)).toBe("0");
    expect(formatProcessIssueQty(2.5)).toBe("2,5");
    expect(formatProcessIssueQty(null)).toBeNull();
    expect(formatProcessIssueQty(undefined)).toBeNull();
  });
});

describe("formatProcessIssueSchedule", () => {
  it("combina data ISO e hora sem deslocamento de fuso", () => {
    expect(formatProcessIssueSchedule("2026-03-15", "07:30:00")).toBe(
      "15/03/2026 · 07:30",
    );
  });

  it("funciona com apenas data ou apenas hora", () => {
    expect(formatProcessIssueSchedule("2026-03-15", null)).toBe("15/03/2026");
    expect(formatProcessIssueSchedule(null, "07:30")).toBe("07:30");
    expect(formatProcessIssueSchedule(null, null)).toBeNull();
  });
});
