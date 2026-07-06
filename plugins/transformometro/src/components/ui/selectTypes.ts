export type SelectOption = {
  value: string;
  label: string;
};

export function mapSelectOptions(
  values: readonly string[],
  labelFor?: (value: string) => string
): SelectOption[] {
  return values.map((value) => ({
    value,
    label: labelFor ? labelFor(value) : value,
  }));
}

export function mapSelectOptionsFromItems<T>(
  items: readonly T[],
  getValue: (item: T) => string,
  getLabel: (item: T) => string
): SelectOption[] {
  return items.map((item) => ({
    value: getValue(item),
    label: getLabel(item),
  }));
}
