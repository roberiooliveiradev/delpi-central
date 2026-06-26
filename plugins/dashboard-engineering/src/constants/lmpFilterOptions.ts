import type { MultiSelectOption } from "../components/MultiSelectField";

export const LMP_LISTING_TYPE_OPTIONS: MultiSelectOption[] = [
  { value: "LMP", label: "LMP" },
  { value: "Amostra", label: "Amostra" },
  { value: "Outro", label: "Outro" },
];

export const LMP_STATUS_OPTIONS: MultiSelectOption[] = [
  { value: "Pontual", label: "Pontual" },
  { value: "Atrasado", label: "Atrasado" },
  { value: "Andamento", label: "Andamento" },
  { value: "Retornada", label: "Retornada" },
];
