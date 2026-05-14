import type { ChatActionCatalogItem } from "../../../data/api/chatTypes";

export type TestField = {
  key: string;
  value: string;
  required?: boolean;
  description?: string;
  location?: "path" | "query";
};

type OpenApiParameter = {
  name?: unknown;
  in?: unknown;
  required?: unknown;
  description?: unknown;
  schema?: unknown;
};

function asParameter(value: unknown): OpenApiParameter | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  return value as OpenApiParameter;
}

function getSchemaType(schema: unknown): string | null {
  if (!schema || typeof schema !== "object" || Array.isArray(schema)) {
    return null;
  }

  const type = (schema as Record<string, unknown>).type;
  return typeof type === "string" ? type : null;
}

function exampleForSchema(schema: unknown): string {
  const type = getSchemaType(schema);

  if (type === "integer" || type === "number") {
    return "0";
  }

  if (type === "boolean") {
    return "false";
  }

  return "";
}

function getParameters(action: ChatActionCatalogItem): OpenApiParameter[] {
  return (action.parametersSchema ?? [])
    .map(asParameter)
    .filter((parameter): parameter is OpenApiParameter => Boolean(parameter));
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
  const parameters = getParameters(action);
  const fromSchema = parameters
    .filter((parameter) => parameter.in === "path")
    .map((parameter) => String(parameter.name ?? ""))
    .filter(Boolean);

  const fromPath = Array.from((action.path ?? "").matchAll(/\{([^}]+)\}/g))
    .map((match) => match[1])
    .filter(Boolean);

  const names = Array.from(new Set([...fromSchema, ...fromPath]));

  return names.map((key) => {
    const parameter = parameters.find(
      (item) => item.in === "path" && item.name === key,
    );

    return {
      key,
      value: exampleForSchema(parameter?.schema),
      required: true,
      description:
        typeof parameter?.description === "string" ? parameter.description : undefined,
      location: "path",
    };
  });
}

export function createInitialQueryFields(action: ChatActionCatalogItem): TestField[] {
  return getParameters(action)
    .filter((parameter) => parameter.in === "query")
    .map((parameter) => ({
      key: String(parameter.name ?? ""),
      value: exampleForSchema(parameter.schema),
      required: parameter.required === true,
      description:
        typeof parameter.description === "string" ? parameter.description : undefined,
      location: "query" as const,
    }))
    .filter((field) => field.key.length > 0);
}

function schemaExample(schema: unknown): unknown {
  if (!schema || typeof schema !== "object" || Array.isArray(schema)) {
    return {};
  }

  const record = schema as Record<string, unknown>;

  if (record.example !== undefined) {
    return record.example;
  }

  if (record.default !== undefined) {
    return record.default;
  }

  if (record.type === "array") {
    return [];
  }

  if (record.type !== "object") {
    const type = typeof record.type === "string" ? record.type : null;

    if (type === "integer" || type === "number") {
      return 0;
    }

    if (type === "boolean") {
      return false;
    }

    return "";
  }

  const properties = record.properties;

  if (!properties || typeof properties !== "object" || Array.isArray(properties)) {
    return {};
  }

  return Object.fromEntries(
    Object.entries(properties as Record<string, unknown>).map(([key, value]) => [
      key,
      schemaExample(value),
    ]),
  );
}

export function createInitialBodyText(action: ChatActionCatalogItem): string {
  if (!isBodyMethod(action.method)) {
    return "";
  }

  const requestBody = action.requestBodySchema;

  if (!requestBody || typeof requestBody !== "object") {
    return "{}";
  }

  const content = requestBody.content;

  if (!content || typeof content !== "object" || Array.isArray(content)) {
    return "{}";
  }

  const contentRecord = content as Record<string, unknown>;
  const jsonContent =
    contentRecord["application/json"] ??
    contentRecord["application/*+json"] ??
    Object.values(contentRecord)[0];

  if (!jsonContent || typeof jsonContent !== "object" || Array.isArray(jsonContent)) {
    return "{}";
  }

  const schema = (jsonContent as Record<string, unknown>).schema;
  return JSON.stringify(schemaExample(schema), null, 2);
}
