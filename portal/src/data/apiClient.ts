// src/data/apiClient.ts

export class ApiClient {
  private baseUrl: string;
  private getToken: () => string | undefined;

  constructor(baseUrl: string, getToken: () => string | undefined) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
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
      const errorText = await response.text();
      throw new Error(errorText);
    }

    return response.json();
  }

  public get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" });
  }
}
