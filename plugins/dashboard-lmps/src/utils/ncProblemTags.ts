import { NC_PROBLEM_TAG_DEFAULTS } from "../constants/ncProblemTags";

export type ProblemTagOption = { value: string; label: string };

function normalizeLabel(value: string): string {
  return value.trim();
}

function dedupeLabels(values: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of values) {
    const label = normalizeLabel(raw);
    if (!label) continue;
    const key = label.toLocaleLowerCase("pt-BR");
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(label);
  }
  return out;
}

export function buildProblemTagOptions(
  catalogLabels: string[],
  selectedValues: string[],
): ProblemTagOption[] {
  const merged = dedupeLabels([
    ...NC_PROBLEM_TAG_DEFAULTS,
    ...catalogLabels,
    ...selectedValues,
  ]);
  return merged
    .sort((left, right) => left.localeCompare(right, "pt-BR"))
    .map((label) => ({ value: label, label }));
}

export function formatProblemTagsDisplay(values: string[]): string {
  if (!values.length) return "—";
  return values.join(", ");
}
