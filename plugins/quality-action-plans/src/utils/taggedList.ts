export function formatTaggedList(values?: string[] | null): string {
  return (values ?? []).join(", ");
}

export function parseTaggedList(input: string): string[] {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function parseStoredTaggedList(value?: string | null): string[] {
  if (!value?.trim()) return [];
  return parseTaggedList(value);
}

export function serializeTaggedList(values: string[]): string | undefined {
  const normalized = values.map((item) => item.trim()).filter(Boolean);
  return normalized.length ? normalized.join(", ") : undefined;
}
