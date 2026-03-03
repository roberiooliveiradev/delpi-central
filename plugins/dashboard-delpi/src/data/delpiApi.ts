// src/data/delpiApi.ts

export interface Product {
  code: string;
  description: string;
  group_code: string;
}

export interface ProductDetails {
  code: string;
  description: string;
  group_code: string;
  type?: string;
  unit?: string;
}

export interface PaginatedResult<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ApiSuccessResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export class DelpiApi {
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  private async get<T>(
    url: string,
    timeoutMs = 30000
  ): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(
      () => controller.abort(),
      timeoutMs
    );

    try {
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${this.token}`,
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error("Erro ao consultar API DELPI");
      }

      return await response.json();
    } catch (error: any) {
      if (error?.name === "AbortError") {
        throw new Error("Timeout na API DELPI");
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  async searchProducts(params: {
    code?: string;
    group?: string;
    description?: string;
    page?: number;
    pageSize?: number;
  }) {
    const query = new URLSearchParams();

    if (params.code) query.append("code", params.code);
    if (params.group) query.append("group", params.group);
    if (params.description)
      query.append("description", params.description);

    query.append("page", String(params.page ?? 1));
    query.append("page_size", String(params.pageSize ?? 20));

    return this.get<ApiSuccessResponse<PaginatedResult<Product>>>(
      `/apps/api-delpi/products/search?${query.toString()}`
    );
  }

  async getProducts(page = 1, pageSize = 20) {
    return this.get<
      ApiSuccessResponse<PaginatedResult<Product>>
    >(
      `/apps/api-delpi/products?page=${page}&page_size=${pageSize}`,
      30000
    );
  }

  async getProduct(code: string) {
    return this.get<ApiSuccessResponse<{ produto: ProductDetails }>>(
      `/apps/api-delpi/products/${code}`
    );
  }
}