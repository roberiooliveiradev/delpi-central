export type CustomerInvoiceSituation = "emitted" | "return";

export type CustomerBillingPeriodPreset =
  | "30"
  | "90"
  | "180"
  | "365"
  | "custom";

export type CustomerInvoiceItem = {
  item: string;
  product_code: string;
  product_description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_value: number;
  sales_order: string;
  sales_order_item: string;
  customer_order: string;
};

export type CustomerInvoice = {
  key: string;
  branch: string;
  invoice_number: string;
  invoice_series: string;
  issue_date: string;
  customer_code: string;
  customer_store: string;
  customer_name: string;
  total_value: number;
  situation: CustomerInvoiceSituation | string;
  sales_order: string;
  customer_order: string;
  item_count: number;
  access_key?: string | null;
  carrier?: string | null;
  items: CustomerInvoiceItem[];
};

export type CustomerBillingSummary = {
  total_billed_value: number;
  invoice_count: number;
  last_invoice_date: string | null;
  last_invoice_value: number | null;
};

export type CustomerBillingPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type CustomerBillingData = {
  summary: CustomerBillingSummary;
  invoices: CustomerInvoice[];
  pagination: CustomerBillingPagination;
};

export type CustomerBillingSituationFilter = "all" | "emitted" | "return";
