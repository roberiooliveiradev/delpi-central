// src/data/delpiApi.ts
import { ApiClient } from "./apiClient";

/* =========================
   MODELOS
========================= */

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

export interface SystemStatus {
  status: string;
  version?: string;
}

export interface HealthStatus {
  status: "online" | string;
}

/* =========================
   API
========================= */

export class DelpiApi {
  private client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  /* =========================
     HEALTH
  ========================= */

  getHealth() {
    return this.client.get<HealthStatus>(
      "/apps/api-delpi/health"
    );
  }

  /* =========================
     PRODUTOS (PAGINADO)
  ========================= */

  getProducts(page: number, pageSize: number) {
    return this.client.get<ApiSuccessResponse<PaginatedResult<Product>>>(
      `/apps/api-delpi/products?page=${page}&page_size=${pageSize}`
    );
  }

  /* =========================
     SYSTEM
  ========================= */

  getSystemStatus() {
    return this.client.get<SystemStatus>(
      "/apps/api-delpi/system/status"
    );
  }
}