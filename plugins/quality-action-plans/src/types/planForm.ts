export type PlanFormValues = {
  title: string;
  branch_code: string;
  severity: string;
  status: string;
  customer_name: string;
  product_code: string;
  batch_number: string;
  department: string;
  reported_problem: string;
  failure_mode: string;
};

export type CreatePlanPayload = {
  title: string;
  branch_code: string;
  severity: string;
  status: string;
  customer_name?: string;
  product_code?: string;
  batch_number?: string;
  department?: string;
  reported_problem?: string;
  failure_mode?: string;
};

export function emptyPlanFormValues(): PlanFormValues {
  return {
    title: "",
    branch_code: "01",
    severity: "medium",
    status: "triage",
    customer_name: "",
    product_code: "",
    batch_number: "",
    department: "",
    reported_problem: "",
    failure_mode: "",
  };
}

export function formValuesToPayload(values: PlanFormValues): CreatePlanPayload {
  return {
    title: values.title.trim(),
    branch_code: values.branch_code,
    severity: values.severity,
    status: values.status,
    customer_name: values.customer_name.trim() || undefined,
    product_code: values.product_code.trim() || undefined,
    batch_number: values.batch_number.trim() || undefined,
    department: values.department.trim() || undefined,
    reported_problem: values.reported_problem.trim() || undefined,
    failure_mode: values.failure_mode.trim() || undefined,
  };
}
