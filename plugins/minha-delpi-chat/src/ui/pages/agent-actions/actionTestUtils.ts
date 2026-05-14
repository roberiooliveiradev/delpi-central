import type { ChatActionCatalogItem } from "../../../data/api/chatTypes";

export type TestField = {
  key: string;
  value: string;
};

export function getPathParameterNames(action: ChatActionCatalogItem): string[] {
  const path = action.path ?? "";
  const matches = Array.from(path.matchAll(/\{([^}]+)\}/g));

  return Array.from(new Set(matches.map((match) => match[1]).filter(Boolean)));
}

export function isBodyMethod(method: string | null | undefined): boolean {
  return !["GET", "HEAD"].includes(String(method ?? "GET").toUpperCase());
}

export function fieldsToRecord(fields: TestField[]): Record<string, string> {
  return Object.fromEntries(
    fields
      .map((field) => [field.key.trim(), field.value] as const)
      .filter(([key]) => key.length > 0),
  );
}

export function parseBodyJson(value: string): unknown {
  const trimmed = value.trim();

  if (!trimmed) {
    return undefined;
  }

  return JSON.parse(trimmed) as unknown;
}

export function createInitialPathFields(action: ChatActionCatalogItem): TestField[] {
  return getPathParameterNames(action).map((key) => ({
    key,
    value: "",
  }));
}
