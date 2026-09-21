import type { CommercialTaskDto } from "../../api/worklistApi";

function fold(value: string | null | undefined): string {
  return (value ?? "").trim().toLocaleLowerCase("pt-BR");
}

export function commercialTaskSearchBlob(
  task: CommercialTaskDto,
  extras: { assigneeLabels?: readonly string[]; typeLabel?: string | null },
): string {
  const customers = [
    task.customer_name,
    task.customer_code,
    ...(task.customers ?? []).flatMap((customer) => [customer.customer_name, customer.customer_code]),
  ];
  const groups = (task.assignee_groups ?? []).map((group) => group.name);
  return [task.title, task.description, extras.typeLabel, ...(extras.assigneeLabels ?? []), ...customers, ...groups]
    .map((part) => fold(part))
    .filter(Boolean)
    .join(" ");
}

export function commercialTaskMatchesQuery(
  task: CommercialTaskDto,
  query: string,
  extras: { assigneeLabels?: readonly string[]; typeLabel?: string | null },
): boolean {
  const needle = fold(query);
  if (!needle) return true;
  return commercialTaskSearchBlob(task, extras).includes(needle);
}
