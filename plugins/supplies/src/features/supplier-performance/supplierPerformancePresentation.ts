import type { SupplierPerformance } from "../../api/supplierPerformance";

export function scoreLabel(value: number | null): string {
  return value == null
    ? "—"
    : value.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}

export function countLabel(value: number): string {
  return value.toLocaleString("pt-BR");
}

export const COVERAGE_LABELS: Record<SupplierPerformance["status"], string> = {
  complete: "IDF calculado",
  missing_quality: "Sem inspeções concluídas",
  missing_delivery: "Sem recebimentos",
  inconsistent: "Dados a revisar",
};

export function supplierKey(item: SupplierPerformance): string {
  return `${item.supplier_code}:${item.supplier_store}`;
}

export function filterSuppliers(
  items: SupplierPerformance[],
  query: string,
  coverage: string,
): SupplierPerformance[] {
  const normalize = (text: string) =>
    text
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("pt-BR");
  const search = normalize(query.trim());
  return items.filter(
    (item) =>
      (!search ||
        normalize(
          `${item.supplier_name} ${item.supplier_code} ${item.supplier_store}`,
        ).includes(search)) &&
      (coverage === "all" ||
        (coverage === "complete"
          ? item.status === "complete"
          : item.status !== "complete")),
  );
}

export function periodLabel(period: { from: string; to: string }): string {
  const format = (iso: string) => iso.split("-").reverse().join("/");
  return `${format(period.from)} a ${format(period.to)}`;
}
