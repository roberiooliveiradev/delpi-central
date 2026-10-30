/** Contrato do BFF `GET /consumption-audit/orders/{op}?unit=01|02` (GLPI #1353).
 * Shape espelha `composite_analysis` do producer — o Portal nunca recalcula.
 */

export type ConsumptionAuditBranch = "01" | "02";

export type ConsumptionAuditTolerancePolicy = {
  id: string;
  absolute: number | null;
  percent: number | null;
};

export type ConsumptionAuditMetadata = {
  contract_version: string;
  generated_at_source: string;
  tolerance_policy: ConsumptionAuditTolerancePolicy;
};

export type ConsumptionAuditOrderInfo = {
  order_number: string;
  order_item: string;
  order_sequence: string;
  order_type: string;
  product_code: string;
  product_description: string;
  product_type: string;
  unit_of_measure: string;
  warehouse: string;
  status: string;
  priority: string;
  planned_quantity: number;
  produced_quantity: number;
  produced_quantity_basis: string;
  emission_date: string;
  planned_start_date: string;
  due_date: string;
  finished_at: string;
};

export type ConsumptionAuditBom = {
  theoretical_quantity: number | null;
  quantity_per_unit: number | null;
  unit_of_measure?: string;
  completeness: string;
  structure_as_of: string;
  reference_date: string;
  valid_from: string;
  valid_to: string;
};

export type ConsumptionAuditCommitment = {
  lines: number;
  original_quantity: number | null;
  open_quantity: number | null;
  derived_consumed_quantity: number | null;
  origin_orders: string[];
};

export type ConsumptionAuditMovement = {
  component_code: string;
  component_type?: string;
  direction: string;
  document: string;
  issue_date: string;
  kind: string;
  cf: string;
  tm: string;
  quantity: number;
  unit_of_measure: string;
  warehouse: string;
  reversed: boolean;
  reason?: string;
};

export type ConsumptionAuditComponent = {
  component_code: string;
  component_description: string;
  component_type: string;
  unit_of_measure: string;
  bom: ConsumptionAuditBom;
  commitment: ConsumptionAuditCommitment;
  movements: {
    classified: ConsumptionAuditMovement[];
    excluded: ConsumptionAuditMovement[];
    eligible_consumption_quantity: number | null;
  };
  discrepancy: {
    reference: string;
    value: number | null;
    within_tolerance: boolean | null;
  };
  classification: string;
  quality_flags: string[];
};

export type ConsumptionAuditSh6Appointment = {
  appointment_id: string;
  channel: string;
  product_code: string;
  resource: string;
  reported_quantity: number | null;
  lost_quantity: number | null;
  reported_at: string;
  started_at: string;
  ended_at: string;
  type: string;
  source: string;
  linked_hza: boolean;
};

export type ConsumptionAuditHzaRecord = {
  appointment_ref: string;
  resource: string;
  started_at: string;
  ended_at: string;
  status: string;
  transaction_type: string;
  source: string;
};

export type ConsumptionAuditSh8Allocation = {
  row_present: boolean;
  source: string;
  status: string | null;
  quantity?: number;
  scheduled_start?: string;
  scheduled_end?: string;
};

export type ConsumptionAuditExecutionEvidence = {
  execution_state: "evidenced" | "pending" | "unknown" | string;
  sh8_allocation: ConsumptionAuditSh8Allocation;
  sh6_appointments: ConsumptionAuditSh6Appointment[];
  hza_records: ConsumptionAuditHzaRecord[];
};

export type ConsumptionAuditOperation = {
  operation: string;
  work_center: string;
  execution_evidence: ConsumptionAuditExecutionEvidence;
  components: ConsumptionAuditComponent[];
};

export type ConsumptionAuditQuality = {
  status: "complete" | "partial" | string;
  warnings: string[];
  unresolved_semantics: string[];
};

export type ConsumptionAuditRelatedOrder = {
  production_order: string;
  relationship: string;
  confidence: string;
  product_code?: string;
  product_type?: string;
  planned_quantity?: number;
  produced_quantity?: number;
  status?: string;
  component_code?: string;
};

export type ConsumptionAuditUnmatchedMovement = ConsumptionAuditMovement & {
  binding: string;
};

export type ConsumptionAuditResponse = {
  production_order: string;
  branch: string;
  metadata: ConsumptionAuditMetadata;
  order: ConsumptionAuditOrderInfo;
  operations: ConsumptionAuditOperation[];
  unmatched_movements: ConsumptionAuditUnmatchedMovement[];
  related_orders: ConsumptionAuditRelatedOrder[];
  quality: ConsumptionAuditQuality;
};

// ——— F1 · busca/listagem paginada (GET /consumption-audit/orders) ———

export type ConsumptionAuditDateType = "emission" | "finished" | "appointment";

export type ConsumptionAuditOrderSummary = {
  production_order: string;
  order_number: string;
  order_item: string;
  order_sequence: string;
  product_code: string;
  product_description: string;
  product_type: string;
  status: string;
  planned_quantity: number;
  produced_quantity: number;
  unit_of_measure: string;
  warehouse: string;
  emission_date: string;
  planned_start_date: string;
  due_date: string;
  finished_at: string;
};

export type ConsumptionAuditSearchPage = {
  items: ConsumptionAuditOrderSummary[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

// ——— F4 · comparação (GET /consumption-audit/comparison) ———

export type ConsumptionAuditComparisonComponent = {
  component_code: string;
  component_description: string;
  component_type: string;
  unit_of_measure: string;
  theoretical_quantity: number | null;
  original_commitment_quantity: number | null;
  open_commitment_quantity: number | null;
  derived_consumption_quantity: number | null;
  eligible_consumption_quantity: number | null;
  difference: number | null;
  classification: string;
  quality_flags: string[];
};

export type ConsumptionAuditComparisonOperation = {
  operation: string;
  work_center: string;
  execution_state: string;
  components: ConsumptionAuditComparisonComponent[];
};

export type ConsumptionAuditUnitTotals = {
  unit_of_measure: string | null;
  theoretical_quantity: number;
  committed_quantity: number;
  open_commitment_quantity: number;
  derived_consumption_quantity: number;
  eligible_consumption_quantity: number;
  components: number;
};

export type ConsumptionAuditComparisonItem = {
  production_order: string;
  branch: string;
  order: ConsumptionAuditOrderInfo;
  operations: ConsumptionAuditComparisonOperation[];
  totals_by_unit: ConsumptionAuditUnitTotals[];
  quality: ConsumptionAuditQuality;
  unmatched_movements_count: number;
  related_orders_count: number;
};

export type ConsumptionAuditComparisonResponse = {
  branch: string;
  items: ConsumptionAuditComparisonItem[];
  not_found: string[];
  metadata: {
    generated_at_source: string;
    comparison_rule: string;
    contract_version: string;
  };
};
