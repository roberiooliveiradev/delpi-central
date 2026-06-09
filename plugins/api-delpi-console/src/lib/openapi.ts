export type OpenApiOperation = {
  id: string;
  method: string;
  path: string;
  summary: string;
  description: string;
  tags: string[];
  parameters: OpenApiParameter[];
  hasBody: boolean;
  requestBodyExample?: string;
  responseStatuses: OpenApiResponseStatus[];
  deprecated: boolean;
};

export type OpenApiParameter = {
  name: string;
  in: "query" | "path" | "header" | "cookie";
  required: boolean;
  schemaType: string;
  description: string;
  example?: string;
};

export type OpenApiResponseStatus = {
  status: string;
  description: string;
  hasExample: boolean;
};

export type OpenApiSpecSummary = {
  title: string;
  version: string;
  openapiVersion: string;
  operationCount: number;
  tagCount: number;
  tags: string[];
};

type OpenApiSpec = {
  openapi?: string;
  info?: { title?: string; version?: string; description?: string };
  paths?: Record<
    string,
    Record<
      string,
      {
        operationId?: string;
        summary?: string;
        description?: string;
        tags?: string[];
        deprecated?: boolean;
        parameters?: Array<{
          name: string;
          in: string;
          required?: boolean;
          description?: string;
          schema?: { type?: string; example?: unknown };
          example?: unknown;
        }>;
        requestBody?: {
          content?: Record<
            string,
            { example?: unknown; schema?: { example?: unknown } }
          >;
        };
        responses?: Record<
          string,
          { description?: string; content?: Record<string, { example?: unknown }> }
        >;
      }
    >
  >;
};

const HTTP_METHODS = ["get", "post", "put", "patch", "delete", "head", "options"];

function schemaExample(param: {
  schema?: { type?: string; example?: unknown };
  example?: unknown;
}): string | undefined {
  const value = param.example ?? param.schema?.example;
  if (value === undefined || value === null) return undefined;
  return String(value);
}

function extractRequestBodyExample(requestBody: unknown): string | undefined {
  if (!requestBody || typeof requestBody !== "object") return undefined;
  const rb = requestBody as {
    content?: Record<string, { example?: unknown; schema?: { example?: unknown } }>;
  };
  const json = rb.content?.["application/json"];
  const example = json?.example ?? json?.schema?.example;
  if (example === undefined || example === null) return undefined;
  return JSON.stringify(example, null, 2);
}

function parseResponses(responses: unknown): OpenApiResponseStatus[] {
  if (!responses || typeof responses !== "object") return [];
  return Object.entries(responses as Record<string, { description?: string; content?: unknown }>)
    .map(([status, meta]) => ({
      status,
      description: meta.description ?? "",
      hasExample: Boolean(meta.content),
    }))
    .sort((a, b) => a.status.localeCompare(b.status));
}

export function parseOpenApiOperations(spec: unknown): OpenApiOperation[] {
  const doc = spec as OpenApiSpec;
  const operations: OpenApiOperation[] = [];

  for (const [path, methods] of Object.entries(doc.paths ?? {})) {
    for (const [method, operation] of Object.entries(methods)) {
      if (!HTTP_METHODS.includes(method)) continue;

      const parameters: OpenApiParameter[] = (operation.parameters ?? []).map((p) => ({
        name: p.name,
        in: p.in as OpenApiParameter["in"],
        required: Boolean(p.required),
        schemaType: p.schema?.type ?? "string",
        description: p.description ?? "",
        example: schemaExample(p),
      }));

      operations.push({
        id: operation.operationId ?? `${method}-${path}`,
        method: method.toUpperCase(),
        path,
        summary: operation.summary ?? operation.operationId ?? path,
        description: operation.description ?? "",
        tags: operation.tags ?? ["sem-tag"],
        parameters,
        hasBody: Boolean(operation.requestBody),
        requestBodyExample: extractRequestBodyExample(operation.requestBody),
        responseStatuses: parseResponses(operation.responses),
        deprecated: Boolean(operation.deprecated),
      });
    }
  }

  return operations.sort((a, b) => {
    const tagCmp = (a.tags[0] ?? "").localeCompare(b.tags[0] ?? "", "pt-BR");
    if (tagCmp !== 0) return tagCmp;
    return a.path.localeCompare(b.path, "pt-BR");
  });
}

export function summarizeOpenApiSpec(spec: unknown): OpenApiSpecSummary {
  const doc = spec as OpenApiSpec;
  const operations = parseOpenApiOperations(spec);
  const tags = new Set<string>();
  for (const op of operations) {
    for (const tag of op.tags) tags.add(tag);
  }

  return {
    title: doc.info?.title ?? "API DELPI",
    version: doc.info?.version ?? "—",
    openapiVersion: doc.openapi ?? "—",
    operationCount: operations.length,
    tagCount: tags.size,
    tags: [...tags].sort((a, b) => a.localeCompare(b, "pt-BR")),
  };
}

export function groupOperationsByTag(
  operations: OpenApiOperation[],
): Map<string, OpenApiOperation[]> {
  const groups = new Map<string, OpenApiOperation[]>();
  for (const op of operations) {
    const tag = op.tags[0] ?? "sem-tag";
    const list = groups.get(tag) ?? [];
    list.push(op);
    groups.set(tag, list);
  }
  return groups;
}

export function buildPathWithParams(
  path: string,
  pathParams: Record<string, string>,
): string {
  let resolved = path;
  for (const [key, value] of Object.entries(pathParams)) {
    resolved = resolved.replace(`{${key}}`, encodeURIComponent(value));
  }
  return resolved;
}
