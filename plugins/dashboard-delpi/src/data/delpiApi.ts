// src/data/delpiApi.ts

export interface Product {
  code: string;
  description: string;
  sale_price?: number;
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

  private async get<T>(url: string): Promise<T> {
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Erro ao consultar API DELPI");
    }

    return response.json();
  }

  async getProducts(page = 1, pageSize = 20) {
    return this.get<ApiSuccessResponse<PaginatedResult<Product>>>(
      `/apps/api-delpi/products?page=${page}&page_size=${pageSize}`
    );
  }
}