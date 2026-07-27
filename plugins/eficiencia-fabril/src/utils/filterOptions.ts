import type { MultiSelectOption } from "../components/MultiSelectField";
import { FACTORY_SHIFTS } from "../constants/shifts";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";

function sortOptions(options: MultiSelectOption[]): MultiSelectOption[] {
  return [...options].sort((left, right) =>
    left.label.localeCompare(right.label, "pt-BR", { sensitivity: "base" })
  );
}

export function buildShiftFilterOptions(): MultiSelectOption[] {
  return FACTORY_SHIFTS.map((shift) => ({
    value: shift.id,
    label: `${shift.label} (${shift.start} – ${shift.end})`,
  }));
}

export function buildOpFilterOptions(items: EficienciaFabrilItem[]): MultiSelectOption[] {
  const values = new Set<string>();

  for (const item of items) {
    const op = item.op?.trim();
    if (op) values.add(op);
  }

  return sortOptions([...values].map((value) => ({ value, label: value })));
}

export function buildFinishedProductFilterOptions(
  items: EficienciaFabrilItem[]
): MultiSelectOption[] {
  const values = new Set<string>();

  for (const item of items) {
    const product = item.produto_acabado?.trim();
    if (product) values.add(product);
  }

  return sortOptions([...values].map((value) => ({ value, label: value })));
}

/**
 * Opções de operação só a partir dos apontamentos dos PAs selecionados
 * (evita lista enorme / custo alto sem PA).
 */
export function buildOperationFilterOptions(
  items: EficienciaFabrilItem[],
  finishedProducts: string[]
): MultiSelectOption[] {
  if (finishedProducts.length === 0) return [];

  const selectedPas = new Set(finishedProducts);
  const options = new Map<string, string>();

  for (const item of items) {
    const pa = item.produto_acabado?.trim();
    if (!pa || !selectedPas.has(pa)) continue;

    const code = item.operacao?.trim();
    if (!code) continue;

    if (!options.has(code)) {
      const description = item.descricao_operacao?.trim();
      options.set(code, description ? `${code} — ${description}` : code);
    }
  }

  return sortOptions(
    [...options.entries()].map(([value, label]) => ({
      value,
      label,
    }))
  );
}

export function buildWorkCenterFilterOptions(items: EficienciaFabrilItem[]): MultiSelectOption[] {
  const values = new Set<string>();

  for (const item of items) {
    const workCenter = item.centro_trabalho?.trim();
    if (workCenter) values.add(workCenter);
  }

  return sortOptions([...values].map((value) => ({ value, label: value })));
}

export function buildEmployeeOptionValue(item: EficienciaFabrilItem): string | null {
  return (
    item.cod_operador?.trim() ||
    item.login_operador?.trim() ||
    item.nome_operador?.trim() ||
    null
  );
}

export function buildEmployeeOptionLabel(item: EficienciaFabrilItem): string {
  const name = item.nome_operador?.trim();
  const login = item.login_operador?.trim();
  const code = item.cod_operador?.trim();

  if (name && login) return `${name} (${login})`;
  if (name && code) return `${name} (${code})`;
  if (name) return name;
  if (login) return login;
  return code ?? "—";
}

export function buildEmployeeFilterOptions(items: EficienciaFabrilItem[]): MultiSelectOption[] {
  const options = new Map<string, string>();

  for (const item of items) {
    const value = buildEmployeeOptionValue(item);
    if (!value) continue;
    if (!options.has(value)) {
      options.set(value, buildEmployeeOptionLabel(item));
    }
  }

  return sortOptions(
    [...options.entries()].map(([value, label]) => ({
      value,
      label,
    }))
  );
}
