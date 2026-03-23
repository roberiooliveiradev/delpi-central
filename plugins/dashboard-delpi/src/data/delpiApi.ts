// src/data/delpiApi.ts

export interface Product {
  code: string;
  description: string;
  group_code: string;
}

export interface ProductDetails {
  code: string
  description: string
  group_code: string
  type?: string
  unit?: string

  [key: string]: any
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
    if (!token) {
      throw new Error("Token de acesso ausente no plugin")
    }
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
    code?: string
    group?: string
    description?: string
    page?: number
    pageSize?: number
    sort?: string
    direction?: "asc" | "desc"
  }) {

    const query = new URLSearchParams()

    if (params.code) query.append("code", params.code)
    if (params.group) query.append("group_code", params.group)
    if (params.description) query.append("description", params.description)

    if (params.sort) query.append("sort", params.sort)
    if (params.direction) query.append("direction", params.direction)

    const page = params.page ?? 1
    const pageSize = params.pageSize ?? 20

    query.append("page", String(page))
    query.append("page_size", String(pageSize))

    return this.get<
      ApiSuccessResponse<PaginatedResult<Product>>
    >(`/apps/api-delpi/products/search?${query.toString()}`)
  }
  
  async getProducts(page = 1, pageSize = 20) {
    return this.searchProducts({
      page,
      pageSize,
    });
  }

  async getProduct(code: string) {

    const query = new URLSearchParams()

    query.append("code", code)
    query.append("page", "1")
    query.append("page_size", "1")

    const response = await this.get<
      ApiSuccessResponse<PaginatedResult<ProductDetails>>
    >(`/apps/api-delpi/products/search?${query.toString()}`)

    const product = response.data.items?.[0]

    if (!product) {
      throw new Error("Produto não encontrado")
    }

    return {
      ...response,
      data: {
        produto: product
      }
    }
  }
}