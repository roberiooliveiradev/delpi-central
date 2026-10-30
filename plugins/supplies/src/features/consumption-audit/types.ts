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
