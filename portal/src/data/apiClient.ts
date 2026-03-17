// src/data/apiClient.ts

export type ApiErrorItem = {
  code: string;
  message: string;
  path?: string;
};

export class HttpError extends Error {
  public status: number;
  public errors: ApiErrorItem[];
  public body?: any;

  constructor(
    status: number,
    message: string,
    errors: ApiErrorItem[] = [],
    body?: any
  ) {
    super(message);
    this.status = status;
    this.errors = errors;
    this.body = body;
  }
}

export class ApiClient {
  private baseUrl: string;
  private getToken: () => string | undefined;

  constructor(baseUrl: string, getToken: () => string | undefined) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: token ? `Bearer ${token}` : "",
        ...(options.headers || {}),
      },
    });

    if (response.status === 401) {
      console.error("Não autorizado — token inválido ou expirado");
      window.location.reload();
      throw new Error("Unauthorized");
    }

    if (!response.ok) {
      const contentType = response.headers.get("content-type") || "";

      let body: any = null;
      let errors: ApiErrorItem[] = [];
      let message = `HTTP ${response.status}`;

      try {
        if (contentType.includes("application/json")) {
          body = await response.json();

          if (Array.isArray(body?.errors)) {
            errors = body.errors;
            message =
              errors.map((e: ApiErrorItem) => e.message).join(", ") || message;
          } else if (body?.message) {
            message = body.message;
          }
        } else {
          const text = await response.text();
          message = text || message;
        }
      } catch {
        // ignore parse errors
      }

      throw new HttpError(response.status, message, errors, body);
    }

    // 204 No Content
    if (response.status === 204) return undefined as T;

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return response.json();
    }

    // fallback (caso algum endpoint retorne texto)
    return (await response.text()) as unknown as T;
  }

  public get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" });
  }

  public post<T>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  public put<T>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  public delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }
}
