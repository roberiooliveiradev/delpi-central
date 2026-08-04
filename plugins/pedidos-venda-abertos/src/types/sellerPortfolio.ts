export type SellerCustomer = {
  customer_code: string;
  customer_store: string;
  customer_name: string | null;
};

export type SellerCustomerInput = {
  customer_code: string;
  customer_store: string;
  customer_name?: string | null;
};

export type SellerPortfolio = {
  id: string;
  user_id: string;
  display_name: string;
  active: boolean;
  customer_count: number;
  customers: SellerCustomer[];
};

export type SellerPortfolioMeResponse = {
  portfolio: SellerPortfolio | null;
  is_admin: boolean;
};

export type PortfolioMeta = {
  empty: boolean;
  message: string | null;
  seller_id: string | null;
};
