export type PlanFormValues = {
  title: string;
  branch_code: string;
  nonconformity_scope: string;
  customer_template: string;
  client_nc_registry: string;
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
  nonconformity_scope: string;
  severity: string;
  status: string;
  customer_name?: string;
  product_code?: string;
  batch_number?: string;
  department?: string;
  reported_problem?: string;
  failure_mode?: string;
};

export type UpdatePlanPayload = {
  title?: string;
  customer_name?: string;
  customer_contact?: string;
  product_code?: string;
  product_description?: string;
  batch_number?: string;
  department?: string;
  reported_problem?: string;
  failure_mode?: string;
  severity?: string;
  branch_code?: string;
  nonconformity_scope?: string;
  client_nc_registry?: string;
  customer_template?: string;
};

export function emptyPlanFormValues(): PlanFormValues {
  return {
    title: "",
    branch_code: "01",
    nonconformity_scope: "external",
    customer_template: "generic",
    client_nc_registry: "",
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
    nonconformity_scope: values.nonconformity_scope,
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
