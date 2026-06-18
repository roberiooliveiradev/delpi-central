export type MeasurementSource = "QEQ" | "QES";

export type InspecoesEntradaHistoricoDetalheTest = {
  test_code: string;
  test_name: string | null;
  expected_specification: string | null;
  text_specification: string | null;
  nominal_value: string | null;
  lower_spec_limit: string | null;
  upper_spec_limit: string | null;
  lower_control_limit: string | null;
  upper_control_limit: string | null;
  min_max_rule: string | null;
  specification_unit: string | null;
  text_measured_value: string | null;
  numeric_measured_value: string | null;
  numeric_measurement_indicator: string | null;
  measured_value: string | null;
  measurement_source: MeasurementSource | null;
  result_code: string;
  result: string;
  measurement_date: string | null;
  measurement_time: string | null;
  sample_number: number | null;
  laboratory: string | null;
  qer_key: string | null;
  sequence_number: string | null;
  inspector_registration: string;
  inspector_name: string;
  inspector_login: string;
};

export type InspecoesEntradaHistoricoDetalheSummary = {
  result: string;
  inspection_status: string;
  report_code: string;
  received_date: string | null;
  received_time: string | null;
  report_date: string | null;
  report_time: string | null;
  invoice_number: string;
  invoice_series: string;
  invoice_item: string;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  product_code: string;
  product_description?: string | null;
  lot: string;
  supplier_lot: string;
  quantity: number;
  unit: string;
  approved_quantity: number | null;
  rejected_quantity: number | null;
  report_justification: string;
  inspector_registration: string;
  inspector_name: string;
  inspector_login: string;
  tests_count: number;
  failed_tests_count: number;
  is_approved: boolean;
  is_rejected: boolean;
};

export type InspecoesEntradaHistoricoDetalheTotals = {
  tests_count: number;
  approved_tests_count: number;
  failed_tests_count: number;
};

export type InspecoesEntradaHistoricoDetalhe = {
  branch: string;
  inspection_id: string;
  summary: InspecoesEntradaHistoricoDetalheSummary;
  tests: InspecoesEntradaHistoricoDetalheTest[];
  totals: InspecoesEntradaHistoricoDetalheTotals;
};

export type FetchHistoricoDetalheParams = {
  branch: string;
  inspection_id: string;
};
