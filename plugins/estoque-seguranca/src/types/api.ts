export type ApiDelpiEnvelope<T> = {
  success: boolean;
  data: T;
  message?: string;
  meta?: {
    operationId?: string;
    entity?: string;
    shape?: string;
    pagination?: {
      page?: number;
      page_size?: number;
      total?: number;
      total_pages?: number;
    };
  };
  error?: { code?: string; message?: string };
};

export type ApiErrorKind = "auth" | "forbidden" | "validation" | "unavailable" | "unknown";

export type ApiClientErrorOptions = {
  code?: string;
  context?: string;
  retryable?: boolean;
};

export class ApiClientError extends Error {
  readonly status: number;
  readonly kind: ApiErrorKind;
  readonly code?: string;
  readonly context?: string;
  readonly retryable: boolean;

  constructor(
    message: string,
    status: number,
    kind: ApiErrorKind,
    options: ApiClientErrorOptions = {},
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.kind = kind;
    this.code = options.code;
    this.context = options.context;
    this.retryable = options.retryable ?? defaultRetryable(kind);
  }
}

function defaultRetryable(kind: ApiErrorKind): boolean {
  return kind === "unavailable" || kind === "unknown";
}

export type SectionErrorState = {
  title: string;
  message: string;
  retryable: boolean;
};

export function resolveApiErrorTitle(kind: ApiErrorKind): string {
  switch (kind) {
    case "auth":
      return "Sessão expirada";
    case "forbidden":
      return "Acesso negado";
    case "validation":
      return "Filtros inválidos";
    case "unavailable":
      return "Dados temporariamente indisponíveis";
    default:
      return "Não foi possível carregar os dados";
  }
}

export function toSectionError(error: unknown): SectionErrorState {
  if (error instanceof ApiClientError) {
    return {
      title: resolveApiErrorTitle(error.kind),
      message: error.message,
      retryable: error.retryable,
    };
  }

  if (error instanceof Error) {
    return {
      title: "Não foi possível carregar os dados",
      message: error.message,
      retryable: true,
    };
  }

  return {
    title: "Não foi possível carregar os dados",
    message: "Falha ao carregar os dados.",
    retryable: true,
  };
}

export function unwrapApiDelpiEnvelope<T>(payload: unknown): T {
  if (!payload || typeof payload !== "object") {
    throw new ApiClientError("Resposta inválida da API.", 0, "unknown");
  }

  const envelope = payload as ApiDelpiEnvelope<T>;

  if (envelope.success === false) {
    throw new ApiClientError(
      envelope.error?.message ?? envelope.message ?? "Falha ao consultar a API.",
      0,
      "unknown",
      { code: envelope.error?.code },
    );
  }

  if (!("data" in envelope)) {
    throw new ApiClientError("Resposta da API sem campo data.", 0, "unknown");
  }

  return envelope.data;
}
