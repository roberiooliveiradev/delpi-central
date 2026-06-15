import type { MultiSelectOption } from "../components/MultiSelectField";
import type { ProductionOeeAppointmentItem } from "../types/production";

function sortOptions(options: MultiSelectOption[]): MultiSelectOption[] {
  return [...options].sort((left, right) =>
    left.label.localeCompare(right.label, "pt-BR", { sensitivity: "base" })
  );
}

export function buildOpFilterOptions(
  items: ProductionOeeAppointmentItem[]
): MultiSelectOption[] {
  const values = new Set<string>();

  for (const item of items) {
    const op = item.production_order?.trim();
    if (op) values.add(op);
  }

  return sortOptions([...values].map((value) => ({ value, label: value })));
}

export function buildWorkCenterFilterOptions(
  items: ProductionOeeAppointmentItem[]
): MultiSelectOption[] {
  const values = new Set<string>();

  for (const item of items) {
    const workCenter = item.work_center?.trim();
    if (workCenter) values.add(workCenter);
  }

  return sortOptions([...values].map((value) => ({ value, label: value })));
}

export function buildOperatorFilterOptions(
  items: ProductionOeeAppointmentItem[]
): MultiSelectOption[] {
  const values = new Set<string>();

  for (const item of items) {
    const operatorCode = item.operator_code?.trim();
    if (operatorCode) values.add(operatorCode);
  }

  return sortOptions([...values].map((value) => ({ value, label: value })));
}
