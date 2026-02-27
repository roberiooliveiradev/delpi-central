// src/data/delpiApi.ts

import { ApiClient } from "./apiClient";

export class DelpiApi {
  private client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  getProducts() {
    return this.client.get<any>("/apps/api-delpi/products");
  }

  getSystemStatus() {
    return this.client.get<any>("/apps/api-delpi/system/status");
  }
}