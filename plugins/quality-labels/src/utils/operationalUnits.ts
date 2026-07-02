export type OperationalUnitOption = { value: string; label: string };

const UNIT_NAMES: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

export const OPERATIONAL_UNIT_OPTIONS: OperationalUnitOption[] = [
  { value: "01", label: "Santa Catarina" },
  { value: "02", label: "Espírito Santo" },
];

export function formatOperationalUnit(
  code: string | null | undefined,
  fallback = "—",
): string {
  const trimmed = (code ?? "").trim();
  if (!trimmed) return fallback;
  return UNIT_NAMES[trimmed] ?? trimmed;
}
