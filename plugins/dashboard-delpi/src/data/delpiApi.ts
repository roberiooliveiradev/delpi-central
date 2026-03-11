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
    if (params.group) query.append("group_code", params.group);
    if (params.description)
      query.append("description", params.description);

    const page = params.page ?? 1;
    const pageSize = params.pageSize ?? 20;

    query.append("page", String(page));
    query.append("page_size", String(pageSize));

    return this.get<
      ApiSuccessResponse<PaginatedResult<Product>>
    >(
      `/apps/api-delpi/products/search?${query.toString()}`
    );
  }

  async getProducts(page = 1, pageSize = 20) {
    return this.searchProducts({
      page,
      pageSize,
    });
  }

  async getProduct(code: string) {
    const response = await this.get<
      ApiSuccessResponse<ProductDetails | { produto: ProductDetails }>
    >(`/apps/api-delpi/products/${code}`);

    const data = response.data as any;

    // Compatibilidade com formato antigo
    if (data?.produto) {
      return response as ApiSuccessResponse<{ produto: ProductDetails }>;
    }

    // Novo formato da API
    return {
      ...response,
      data: {
        produto: data as ProductDetails,
      },
    };
  }
}