import type { MultiSelectOption } from "../components/forms/MultiSelectField";

export function buildMultiSelectTriggerLabel(
  selectedValues: string[],
  options: MultiSelectOption[],
  emptyLabel: string,
  multipleSelectedLabel: (count: number) => string,
): string {
  if (selectedValues.length === 0) return emptyLabel;
  if (selectedValues.length === 1) {
    return options.find((option) => option.value === selectedValues[0])?.label ?? selectedValues[0];
  }
  return multipleSelectedLabel(selectedValues.length);
}
