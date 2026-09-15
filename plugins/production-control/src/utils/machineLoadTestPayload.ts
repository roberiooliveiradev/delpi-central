import type { MachineLoadOperation, MachineLoadPayload } from "../types";

/** Fila mínima com dois centros — base dos testes de recorte e de status vivo. */
export function makeMachineLoadOperation(
  overrides: Partial<MachineLoadOperation> = {},
): MachineLoadOperation {
  return {
    branch: "01",
    work_center: "CT-01A",
    work_center_name: "CORTE E DECAPE",
    scheduled_date: "2026-08-20",
    scheduled_start_time: "05:00",
    production_order: "24640401002",
    operation_code: "03",
    operation_description: "CORTAR E APLICAR",
    tool: "23-B31",
    is_manual_operation: false,
    product_code: "50320064",
    product_description: "CF1,5BRAN",
    unit: "PC",
    planned_qty: 7.1,
    pending_qty: 7.1,
    pa_due_date: "2026-08-21",
    pa_product_code: "PA-1",
    production_status: "not_started",
    is_in_production: false,
    production_started_date: null,
    production_started_time: null,
    active_operator_code: null,
    active_operator_name: null,
    active_operator_count: 0,
    appointment_count: 0,
    last_appointment_date: null,
    ...overrides,
  };
}

export function makeMachineLoadPayload(
  overrides: Partial<MachineLoadPayload> = {},
): MachineLoadPayload {
  const operations = [
    makeMachineLoadOperation({ work_center: "CT-01A", production_order: "24640401002" }),
    makeMachineLoadOperation({ work_center: "CT-01A", production_order: "24640401003" }),
    makeMachineLoadOperation({
      work_center: "CT-02",
      work_center_name: "APLICAÇÃO DE TERMINAIS",
      production_order: "24640401010",
    }),
  ];
  return {
    branch: "01",
    period: { start_date: null, end_date: "2026-09-02" },
    summary: {
      work_center_count: 2,
      operation_count: operations.length,
      order_count: 3,
      in_production_count: 0,
    },
    snapshot: { refreshed_at: "2026-08-19T22:00:00Z", seeded: false },
    work_centers: [
      {
        work_center: "CT-01A",
        work_center_name: "CORTE E DECAPE",
        operation_count: 2,
        order_count: 2,
        in_production_count: 0,
      },
      {
        work_center: "CT-02",
        work_center_name: "APLICAÇÃO DE TERMINAIS",
        operation_count: 1,
        order_count: 1,
        in_production_count: 0,
      },
    ],
    operations,
    selected: {
      work_center: "CT-01A",
      requested_work_center: null,
      items: operations.filter((item) => item.work_center === "CT-01A"),
      pagination: { page: 1, page_size: 2, total: 2, is_complete: true },
    },
    ...overrides,
  };
}
