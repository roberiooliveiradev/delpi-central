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

type ApiClientOptions = {
  refreshToken?: () => Promise<boolean>;
  onUnauthorized?: () => void | Promise<void>;
};

export class ApiClient {
  private baseUrl: string;
  private getToken: () => string | undefined;
  private refreshTokenFn?: () => Promise<boolean>;
  private onUnauthorized?: () => void | Promise<void>;

  constructor(
    baseUrl: string,
    getToken: () => string | undefined,
    options?: ApiClientOptions
  ) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
    this.refreshTokenFn = options?.refreshToken;
    this.onUnauthorized = options?.onUnauthorized;
  }

  private async doFetch(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const token = this.getToken();

    return fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    });
  }

  private async parseError(response: Response): Promise<never> {
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

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    hasRetried = false
  ): Promise<T> {
    const response = await this.doFetch(endpoint, options);

    if (response.status === 401) {
      if (!hasRetried && this.refreshTokenFn) {
        try {
          const refreshed = await this.refreshTokenFn();

          if (refreshed) {
            return this.request<T>(endpoint, options, true);
          }
        } catch {
          // segue para unauthorized controlado
        }
      }

      if (this.onUnauthorized) {
        await this.onUnauthorized();
      }

      throw new HttpError(401, "Unauthorized");
    }

    if (!response.ok) {
      return this.parseError(response);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      return response.json();
    }

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