import { describe, expect, it } from "vitest";

import type { MachineLoadOperation, PcpOperatorFeedback } from "../types";
import {
  countOperationsWithFeedback,
  feedbackMaterialStatusLabel,
  hasUndeliveredMaterials,
  feedbackForOperation,
  feedbackReasonLabel,
  feedbackStatusLabel,
  feedbackTypeLabel,
  filterOperationsWithFeedback,
  findOperationInQueue,
  indexFeedbackByOperation,
  normalizeOperationCode,
  operatorFeedbackKey,
} from "./operatorFeedback";

function makeFeedback(
  partial: Partial<PcpOperatorFeedback> = {},
): PcpOperatorFeedback {
  return {
    id: "fb-1",
    branch: "01",
    productionOrder: "24640401002",
    operationCode: "03",
    reportedWorkCenter: "CT-63",
    feedbackType: "cannot_produce",
    reasonCode: "missing_material",
    note: null,
    status: "open",
    operatorCode: "001234",
    operatorName: "Maria Silva",
    productCode: "TR-1",
    productDescription: null,
    paProductCode: "PA-9",
    dueDate: "2026-10-08",
    createdAt: "2026-10-01T08:00:00Z",
    acknowledgedAt: null,
    acknowledgedBy: null,
    ...partial,
  };
}

function makeOperation(
  partial: Partial<MachineLoadOperation> = {},
): MachineLoadOperation {
  return {
    branch: "01",
    work_center: "CT-64",
    work_center_name: "Bancada 64",
    scheduled_date: null,
    scheduled_start_time: null,
    production_order: "24640401002",
    operation_code: "03",
    operation_description: "Montagem",
    tool: "",
    is_manual_operation: false,
    product_code: "TR-1",
    product_description: "Trafo",
    unit: null,
    planned_qty: 10,
    pending_qty: 10,
    pa_due_date: null,
    pa_product_code: null,
    production_status: "not_started",
    is_in_production: false,
    production_started_date: null,
    production_started_time: null,
    active_operator_code: null,
    active_operator_name: null,
    active_operator_count: 0,
    appointment_count: 0,
    last_appointment_date: null,
    ...partial,
  };
}

describe("operatorFeedbackKey", () => {
  it("associa por OP + operacao, sem o centro reportado", () => {
    const feedback = makeFeedback({ reportedWorkCenter: "CT-63" });
    const rowInOtherCenter = makeOperation({ work_center: "CT-64" });
    const map = indexFeedbackByOperation([feedback]);
    expect(feedbackForOperation(map, rowInOtherCenter)?.id).toBe("fb-1");
  });

  it("normaliza zeros a esquerda como o backend", () => {
    expect(normalizeOperationCode("030")).toBe("30");
    expect(normalizeOperationCode("000")).toBe("0");
    expect(operatorFeedbackKey("24640401002", "030")).toBe(
      operatorFeedbackKey("24640401002", "30"),
    );
  });

  it("diferencia OPs e operacoes distintas", () => {
    expect(operatorFeedbackKey("A", "03")).not.toBe(operatorFeedbackKey("B", "03"));
    expect(operatorFeedbackKey("A", "03")).not.toBe(operatorFeedbackKey("A", "04"));
  });
});

describe("feedbackStatusLabel", () => {
  it("open -> Aguardando tratativa", () => {
    expect(feedbackStatusLabel("open")).toBe("Aguardando tratativa");
  });
  it("acknowledged -> Em tratativa", () => {
    expect(feedbackStatusLabel("acknowledged")).toBe("Em tratativa");
  });
  it("status desconhecido cai no rotulo de open (fallback seguro)", () => {
    expect(feedbackStatusLabel("xyz")).toBe("Aguardando tratativa");
  });
});

describe("labels de tipo e motivo", () => {
  it("missing_material tem label amigavel", () => {
    expect(feedbackReasonLabel("missing_material")).toBe("Falta de matéria-prima");
  });
  it("cannot_produce tem label amigavel", () => {
    expect(feedbackTypeLabel("cannot_produce")).toBe("Não será possível produzir");
  });
  it("codigo desconhecido nao quebra", () => {
    expect(feedbackReasonLabel("other")).toBe("other");
  });
});

describe("filtro e mapa de impedimentos", () => {
  it("filtro Com impedimento so deixa linhas com feedback ativo", () => {
    const map = indexFeedbackByOperation([makeFeedback()]);
    const rows = [
      makeOperation(),
      makeOperation({ production_order: "OTHER", operation_code: "01" }),
    ];
    const filtered = filterOperationsWithFeedback(rows, map);
    expect(filtered).toHaveLength(1);
    expect(filtered[0].production_order).toBe("24640401002");
    expect(countOperationsWithFeedback(rows, map)).toBe(1);
  });

  it("acao em uma OP nao altera a associacao de outra", () => {
    const map = indexFeedbackByOperation([
      makeFeedback({ id: "fb-1" }),
      makeFeedback({ id: "fb-2", productionOrder: "OTHER", operationCode: "01" }),
    ]);
    const other = makeOperation({ production_order: "OTHER", operation_code: "01" });
    expect(feedbackForOperation(map, other)?.id).toBe("fb-2");
    map.delete(operatorFeedbackKey("24640401002", "03"));
    expect(feedbackForOperation(map, other)?.id).toBe("fb-2");
  });
});

describe("findOperationInQueue", () => {
  it("acha a operacao no CT atual mesmo reportada em outro", () => {
    const feedback = makeFeedback({ reportedWorkCenter: "CT-63" });
    const op = makeOperation({ work_center: "CT-64" });
    expect(findOperationInQueue([op], feedback)?.work_center).toBe("CT-64");
  });

  it("fora da fila retorna null (feedback continua na inbox)", () => {
    expect(findOperationInQueue([makeOperation()], makeFeedback({
      productionOrder: "OUTRA",
    }))).toBeNull();
  });
});


describe("feedbackMaterialStatusLabel", () => {
  it("mapeia pending/picked/delivered", () => {
    expect(feedbackMaterialStatusLabel("pending")).toBe("Aguardando separação");
    expect(feedbackMaterialStatusLabel("picked")).toBe("Em separação");
    expect(feedbackMaterialStatusLabel("delivered")).toBe("Entregue");
  });

  it("status desconhecido cai no fallback de pendente", () => {
    expect(feedbackMaterialStatusLabel("future")).toBe("Aguardando separação");
  });
});

describe("hasUndeliveredMaterials", () => {
  it("false quando não há materiais (legado)", () => {
    expect(hasUndeliveredMaterials(makeFeedback())).toBe(false);
    expect(
      hasUndeliveredMaterials(makeFeedback({ materials: [] })),
    ).toBe(false);
  });

  it("true com pending ou picked", () => {
    const pending = makeFeedback({
      materials: [
        {
          id: "m1",
          productCode: "10081234",
          description: "TERMINAL",
          unit: "PC",
          openQty: 10,
          status: "pending",
          pickedAt: null,
          deliveredAt: null,
        },
      ],
    });
    expect(hasUndeliveredMaterials(pending)).toBe(true);
  });

  it("false quando todos entregues", () => {
    const done = makeFeedback({
      materials: [
        {
          id: "m1",
          productCode: "10081234",
          description: "TERMINAL",
          unit: "PC",
          openQty: 10,
          status: "delivered",
          pickedAt: "2026-10-01T09:00:00Z",
          deliveredAt: "2026-10-01T09:30:00Z",
        },
      ],
    });
    expect(hasUndeliveredMaterials(done)).toBe(false);
  });
});
