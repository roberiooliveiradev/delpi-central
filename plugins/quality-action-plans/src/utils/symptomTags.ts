export function formatSymptomTags(tags?: string[] | null): string {
  return (tags ?? []).join(", ");
}

export function parseSymptomTags(input: string): string[] {
  return input
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export function formatEffectivenessRate(rate?: number | null): string {
  if (rate == null || Number.isNaN(rate)) return "—";
  return `${Math.round(rate * 100)}%`;
}
