import type { MultiSelectOption } from "../components/MultiSelectField";

export const LMPS_BRANCH_OPTIONS: MultiSelectOption[] = [
  { value: "01", label: "01" },
  { value: "02", label: "02" },
];

export const LMPS_LISTING_TYPE_OPTIONS: MultiSelectOption[] = [
  { value: "LMP", label: "LMP" },
  { value: "Amostra", label: "Amostra" },
  { value: "Outro", label: "Outro" },
];

export const LMPS_STATUS_OPTIONS: MultiSelectOption[] = [
  { value: "Pontual", label: "Pontual" },
  { value: "Atrasado", label: "Atrasado" },
  { value: "Andamento", label: "Andamento" },
  { value: "Retornada", label: "Retornada" },
];
